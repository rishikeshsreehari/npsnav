"""Repair NAVs stored under day/month-swapped dates.

A past import (commit d96123551, Jun 2025) read day-first dates as month-first, so
some scheme files hold e.g. 4 Jun 2025's NAV under 04/06/2025 (= 6 Apr, a Sunday),
or 11 Apr 2016's NAV under 11/04/2016 (= 4 Nov 2016, a real trading day).

For every scheme with a stored NAV that is an exact copy of the NAV at its swapped
date on a suspicious date, the full history is fetched from the NPS Trust per-scheme
endpoint (rows before Apr 2026 carry the correct SCHEME ID) and each entry is:
  - replaced with NPS Trust's value when NPS Trust has that date with a different NAV;
  - deleted when it is not a NAV date at all (no fetched scheme has a NAV that day),
    or when it is flagged as a weekend/spike copy and NPS Trust has no value for it;
  - otherwise left alone.

Usage:
  python scripts/repair_swapped_dates.py            # dry run, prints the plan
  python scripts/repair_swapped_dates.py --apply    # writes the scheme files
"""

import argparse
import concurrent.futures
import glob
import json
import os
import time
from collections import OrderedDict, defaultdict
from datetime import datetime
from io import StringIO

import pandas as pd
import requests
import urllib3

try:
    from .nav_validation import filter_rows_for_scheme, find_swapped_date_copies, parse_nav
except ImportError:
    from nav_validation import filter_rows_for_scheme, find_swapped_date_copies, parse_nav

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATE_FORMAT = "%m/%d/%Y"
BASE_URL = "https://npstrust.org.in/scheme-wise-nav-report-excel"
FULL_HISTORY = "2"  # navyearselxls value that returns the full history (back to 2008)


def parse(d):
    return datetime.strptime(d, DATE_FORMAT)


def swapped(date):
    month, day, year = date.split("/")
    if month == day or int(day) > 12:
        return None
    return f"{day}/{month}/{year}"


def load_histories():
    histories = {}
    for path in sorted(glob.glob("data/SM*.json")):
        with open(path) as f:
            histories[os.path.basename(path)[:-5]] = json.load(f, object_pairs_hook=OrderedDict)
    return histories


def copies_on(history, dates):
    """Entries on the given dates whose NAV equals the NAV at the swapped date."""
    out = []
    for date in dates:
        s = swapped(date)
        if date in history and s and s in history and float(history[s]) == float(history[date]):
            out.append(date)
    return out


def fetch_nps_history(scheme_code, retries=3):
    """Full NPS Trust history for one scheme as {MM/DD/YYYY: nav}, or None on failure."""
    params = {"navcatdataxls": f"PFM{scheme_code[2:5]}", "navyearselxls": FULL_HISTORY,
              "navsubdataxls": scheme_code}
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://npstrust.org.in/"}
    for attempt in range(retries):
        try:
            r = requests.get(BASE_URL, params=params, headers=headers, verify=False, timeout=90)
            if r.status_code == 200 and len(r.content) > 100:
                df = pd.read_csv(StringIO(r.content.decode("utf-8", errors="ignore")), sep="\t")
                df = filter_rows_for_scheme(df, scheme_code)
                out = {}
                for _, row in df.iterrows():
                    nav = parse_nav(row.get("NAV VALUE"))
                    try:
                        d = datetime.strptime(str(row.get("DATE OF NAV")).strip(), "%Y-%m-%d")
                    except ValueError:
                        continue
                    if nav:
                        out[d.strftime(DATE_FORMAT)] = nav
                return out
        except (requests.RequestException, ValueError, KeyError):
            pass
        time.sleep(2 ** attempt)
    return None


def covers(nps, date, days=7):
    """True if NPS Trust has NAVs for this scheme within `days` on both sides of date."""
    target = parse(date)
    before = after = False
    for d in nps:
        delta = (parse(d) - target).days
        before |= -days <= delta < 0
        after |= 0 < delta <= days
        if before and after:
            return True
    return False


def plan_repairs(histories, nps_by_scheme, suspicious_dates, flagged):
    """Return {scheme: [(date, action, old, new)]}; action is 'replace' or 'delete'."""
    nav_dates = set()  # dates on which at least one fetched scheme has an NPS Trust NAV
    for nps in nps_by_scheme.values():
        if nps:
            nav_dates.update(nps)
    plan = defaultdict(list)
    for code, history in histories.items():
        nps = nps_by_scheme.get(code)
        for date in copies_on(history, suspicious_dates):
            old = history[date]
            is_flagged = date in flagged.get(code, ())
            if nps and date in nps:
                if float(nps[date]) != float(old):
                    plan[code].append((date, "replace", old, nps[date]))
            elif date not in nav_dates:
                plan[code].append((date, "delete", old, None))  # not a NAV date at all
            elif is_flagged:
                # Clearly another day's NAV (weekend or one-day spike) and no source for the
                # right value: a gap is better than a wrong NAV.
                plan[code].append((date, "delete", old, None))
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write changes to data/SM*.json")
    args = parser.parse_args()

    histories = load_histories()
    flagged = {code: set(find_swapped_date_copies(h)) for code, h in histories.items()}
    flagged = {code: dates for code, dates in flagged.items() if dates}
    suspicious_dates = sorted({d for dates in flagged.values() for d in dates}, key=parse)
    print(f"Suspicious dates: {suspicious_dates}")

    to_check = sorted(code for code, h in histories.items() if copies_on(h, suspicious_dates))
    print(f"Fetching NPS Trust history for {len(to_check)} schemes...")
    nps_by_scheme = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for code, nps in zip(to_check, pool.map(fetch_nps_history, to_check)):
            nps_by_scheme[code] = nps
    failed = [c for c, n in nps_by_scheme.items() if n is None]
    if failed:
        print(f"WARNING: fetch failed for {failed}; only flagged copies on non-NAV dates are touched for them")

    plan = plan_repairs(histories, nps_by_scheme, suspicious_dates, flagged)
    summary = defaultdict(lambda: defaultdict(int))
    for code, actions in plan.items():
        for date, action, old, new in actions:
            summary[date][action] += 1
    for date in sorted(summary, key=parse):
        print(f"  {date} ({parse(date):%a}): " + ", ".join(f"{k} {v}" for k, v in sorted(summary[date].items())))
    print(f"Total: {sum(len(a) for a in plan.values())} entries in {len(plan)} schemes")

    if not args.apply:
        print("Dry run; re-run with --apply to write changes.")
        return plan, nps_by_scheme
    for code, actions in plan.items():
        history = histories[code]
        for date, action, old, new in actions:
            if action == "replace":
                history[date] = new
            else:
                del history[date]
        ordered = OrderedDict(sorted(history.items(), key=lambda kv: parse(kv[0]), reverse=True))
        path = f"data/{code}.json"
        with open(path, "rb") as f:
            newline = "\r\n" if b"\r\n" in f.read(200) else "\n"  # keep the file's line endings
        with open(path, "w", newline=newline) as f:
            json.dump(ordered, f, indent=4)
    print("Applied.")
    return plan, nps_by_scheme


if __name__ == "__main__":
    main()
