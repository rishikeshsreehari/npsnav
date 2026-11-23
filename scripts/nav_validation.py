"""Pure helpers for reconciling NAV records from multiple sources."""

import math
import re
from datetime import datetime
from decimal import Decimal


DATE_FORMAT = "%m/%d/%Y"
NAV_TOLERANCE = Decimal("0.0001")


def clean_cell(value):
    """Stringify a source cell, mapping blanks/NaN/None to ''.

    pandas turns empty cells into float NaN, and str(NaN) == 'nan', which would
    otherwise slip through truthiness checks as a real value.
    """
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in ("nan", "none", "null") else text


def parse_nav(value):
    """Return a NAV as a normalized string, or None if blank, non-numeric or not positive."""
    text = clean_cell(value)
    if not text:
        return None
    try:
        nav = float(text)
    except ValueError:
        return None
    if not math.isfinite(nav) or nav <= 0:
        return None
    return str(nav)


def _index_by_date_and_scheme(records_by_date):
    """Return records keyed by their reported (date, scheme code)."""
    return {
        (info["date"], scheme_code): info
        for schemes in records_by_date.values()
        for scheme_code, info in schemes.items()
        if info.get("date")
    }


def compare_nav_sources(protean_by_date, nps_records, tolerance=NAV_TOLERANCE):
    """Compare only records that have the same scheme code and reported date."""
    protean_index = _index_by_date_and_scheme(protean_by_date)
    nps_index = {
        (info["date"], scheme_code): info
        for scheme_code, info in nps_records.items()
        if info.get("date")
    }

    shared_keys = sorted(set(protean_index) & set(nps_index))
    mismatches = []
    for date_scheme in shared_keys:
        date, scheme_code = date_scheme
        protean_nav = protean_index[date_scheme]["nav"]
        nps_nav = nps_index[date_scheme]["nav"]
        difference = abs(Decimal(protean_nav) - Decimal(nps_nav))
        if difference > tolerance:
            mismatches.append((scheme_code, date, protean_nav, nps_nav))

    protean_dates_by_scheme = {}
    for date, scheme_code in protean_index:
        protean_dates_by_scheme.setdefault(scheme_code, set()).add(date)

    different_date_schemes = sorted(
        scheme_code
        for scheme_code, info in nps_records.items()
        if scheme_code in protean_dates_by_scheme
        and info.get("date") not in protean_dates_by_scheme[scheme_code]
    )

    return {
        "shared_count": len(shared_keys),
        "mismatches": mismatches,
        "different_date_schemes": different_date_schemes,
    }


def filter_rows_for_scheme(df, scheme_code):
    """Keep only rows whose SCHEME ID matches scheme_code.

    NPS Trust's per-scheme endpoint returns the DIRECT variant's rows for old POP
    codes (from Apr 2026 onwards), so the requested code can't be trusted blindly.
    DataFrames without a SCHEME ID column are returned unchanged.
    """
    for col in df.columns:
        if str(col).strip().lower() == "scheme id":
            return df[df[col].astype(str).str.strip() == scheme_code]
    return df


def merge_latest_records(existing, new):
    """Keep one data.json record per (PFM Code, Scheme Code): the one with the latest date.

    New records win ties, so a corrected NAV for the already-latest date replaces
    the stale value. Callers must only pass records that were actually written.

    For schemes already in data.json only Date and NAV are taken from the new
    record; names are owned by apply_protean_names() so the source that happened
    to supply a NAV can't flip them.
    """
    latest = {}
    for record in existing:
        latest[(record["PFM Code"], record["Scheme Code"])] = dict(record)
    for record in new:
        key = (record["PFM Code"], record["Scheme Code"])
        current = latest.get(key)
        if current is None:
            latest[key] = dict(record)
        elif _parse_date(record["Date"]) >= _parse_date(current["Date"]):
            current["Date"] = record["Date"]
            current["NAV"] = record["NAV"]
    return list(latest.values())


# --- Protean daily file parsing -------------------------------------------------

SCHEME_CODE_RE = re.compile(r"^SM\d{6}$")


def pick_protean_member(names):
    """Return the NAV .out member of a Protean ZIP, ignoring macOS '__MACOSX/._*' junk."""
    for name in names:
        base = name.rsplit("/", 1)[-1]
        if name.endswith(".out") and not name.startswith("__MACOSX/") and not base.startswith("._"):
            return name
    return None


def parse_protean_line(line):
    """Parse 'date,PFM code,PFM name,scheme code,scheme name,NAV' into a record, or None.

    The scheme code is used as an anchor so a comma inside the PFM or scheme name
    doesn't shift the columns and silently drop the line (and its NAV).
    """
    raw = line.strip().split(",")
    cols = [c.strip() for c in raw]
    if len(cols) < 6:
        return None
    code_idx = next((i for i in range(3, len(cols) - 2) if SCHEME_CODE_RE.match(cols[i])), None)
    if code_idx is None:
        return None
    record_date = cols[0]
    try:
        _parse_date(record_date)
    except ValueError:
        return None
    nav = parse_nav(cols[-1])
    if not nav:
        return None
    return {
        "code": cols[code_idx],
        "nav": nav,
        "date": record_date,
        "pfm_name": ",".join(raw[2:code_idx]).strip(),
        "scheme_name": ",".join(raw[code_idx + 1:-1]).strip(),
    }


# --- Canonical names --------------------------------------------------------------

TIER_RE = re.compile(r"TIER[\s-]*(II|I|1|2)\b", re.IGNORECASE)


def choose_scheme_name(protean_name, current_name, dump_name=None):
    """Pick the canonical scheme name.

    Protean's current names are authoritative (they carry the POP/DIRECT/GS variant
    suffixes; the NPS Trust dump drops POP and uses pre-rename PFM names). Exception:
    when Protean's name omits the tier but another name has it (e.g. ICICI MSF funds),
    keep the tiered name so the scheme doesn't fall out of the Tier filter.
    """
    if not protean_name:
        return current_name
    if TIER_RE.search(protean_name):
        return protean_name
    for fallback in (current_name, dump_name):
        if fallback and TIER_RE.search(fallback):
            return fallback
    return protean_name


def apply_protean_names(records, protean_latest, dump=None):
    """Update Scheme/PFM names in data.json records in place from the newest Protean file.

    records: list of data.json dicts. protean_latest: {code: {scheme_name, pfm_name}}
    from the NEWEST Protean file only (older files predate the POP suffixes).
    dump: optional {code: {scheme_name}} from NPS Trust, used only by the tier guard.
    Schemes absent from Protean keep their names. Returns a list of (code, field, old, new).
    """
    dump = dump or {}
    changes = []
    for record in records:
        info = protean_latest.get(record["Scheme Code"])
        if not info:
            continue
        new_name = choose_scheme_name(
            info.get("scheme_name"),
            record.get("Scheme Name"),
            dump.get(record["Scheme Code"], {}).get("scheme_name"),
        )
        updates = {"Scheme Name": new_name, "PFM Name": info.get("pfm_name") or record.get("PFM Name")}
        for field, value in updates.items():
            if value and record.get(field) != value:
                changes.append((record["Scheme Code"], field, record.get(field), value))
                record[field] = value
    return changes


def _parse_date(date_str):
    return datetime.strptime(date_str, DATE_FORMAT)


def group_records_by_date(protean_by_date, nps_records):
    """Group trusted records by date.

    Protean is authoritative for any (scheme, date) it covers. NPS Trust is used
    for schemes Protean did not return, and for dates strictly newer than the
    latest Protean date for that scheme (Protean often lags NPS Trust by days).
    NPS values for dates at or before Protean's latest are ignored.
    """
    grouped = {}
    protean_latest = {}

    for schemes in protean_by_date.values():
        for scheme_code, info in schemes.items():
            record_date = info.get("date")
            if not record_date:
                continue
            grouped.setdefault(record_date, {})[scheme_code] = info
            parsed = _parse_date(record_date)
            if scheme_code not in protean_latest or parsed > protean_latest[scheme_code]:
                protean_latest[scheme_code] = parsed

    for scheme_code, info in nps_records.items():
        record_date = info.get("date")
        if not record_date:
            continue
        latest = protean_latest.get(scheme_code)
        if latest is not None and _parse_date(record_date) <= latest:
            continue
        grouped.setdefault(record_date, {})[scheme_code] = info

    return grouped
