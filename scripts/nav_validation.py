"""Pure helpers for reconciling NAV records from multiple sources."""

from datetime import datetime
from decimal import Decimal


DATE_FORMAT = "%m/%d/%Y"
NAV_TOLERANCE = Decimal("0.0001")


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
