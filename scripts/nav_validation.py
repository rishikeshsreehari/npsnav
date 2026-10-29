"""Pure helpers for reconciling NAV records from multiple sources."""

from decimal import Decimal


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


def group_records_by_date(protean_by_date, nps_records):
    """Group trusted records by date, using NPS only for Protean-missing schemes."""
    grouped = {}
    protean_scheme_codes = set()

    for schemes in protean_by_date.values():
        for scheme_code, info in schemes.items():
            protean_scheme_codes.add(scheme_code)
            record_date = info.get("date")
            if record_date:
                grouped.setdefault(record_date, {})[scheme_code] = info

    for scheme_code, info in nps_records.items():
        if scheme_code in protean_scheme_codes:
            continue
        record_date = info.get("date")
        if record_date:
            grouped.setdefault(record_date, {})[scheme_code] = info

    return grouped
