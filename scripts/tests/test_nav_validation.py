import unittest

import pandas as pd

from scripts.nav_validation import (
    compare_nav_sources,
    filter_rows_for_scheme,
    group_records_by_date,
)


def nav_record(nav, date, source):
    return {
        "nav": nav,
        "date": date,
        "pfm_name": source,
        "scheme_name": source,
    }


class CompareNavSourcesTests(unittest.TestCase):
    def test_matching_scheme_and_date_passes(self):
        protean = {
            "10/27/2026": {
                "SM001001": nav_record("49.3817", "10/27/2026", "Protean")
            }
        }
        nps = {
            "SM001001": nav_record("49.3817", "10/27/2026", "NPS Trust")
        }

        result = compare_nav_sources(protean, nps)

        self.assertEqual(result["shared_count"], 1)
        self.assertEqual(result["mismatches"], [])
        self.assertEqual(result["different_date_schemes"], [])

    def test_difference_equal_to_tolerance_is_not_a_mismatch(self):
        protean = {
            "10/27/2026": {
                "SM001001": nav_record("10.0000", "10/27/2026", "Protean")
            }
        }
        nps = {
            "SM001001": nav_record("10.0001", "10/27/2026", "NPS Trust")
        }

        result = compare_nav_sources(protean, nps)

        self.assertEqual(result["mismatches"], [])

    def test_same_date_difference_above_tolerance_is_a_mismatch(self):
        protean = {
            "10/27/2026": {
                "SM001001": nav_record("49.3817", "10/27/2026", "Protean")
            }
        }
        nps = {
            "SM001001": nav_record("49.3601", "10/27/2026", "NPS Trust")
        }

        result = compare_nav_sources(protean, nps)

        self.assertEqual(result["shared_count"], 1)
        self.assertEqual(
            result["mismatches"],
            [("SM001001", "10/27/2026", "49.3817", "49.3601")],
        )

    def test_different_dates_are_skipped_not_reported_as_mismatches(self):
        protean = {
            "10/27/2026": {
                "SM001001": nav_record("49.3817", "10/27/2026", "Protean")
            }
        }
        nps = {
            "SM001001": nav_record("49.5000", "10/28/2026", "NPS Trust")
        }

        result = compare_nav_sources(protean, nps)

        self.assertEqual(result["shared_count"], 0)
        self.assertEqual(result["mismatches"], [])
        self.assertEqual(result["different_date_schemes"], ["SM001001"])

    def test_record_date_is_used_instead_of_outer_bucket_date(self):
        protean = {
            "10/29/2026": {
                "SM001001": nav_record("49.3817", "10/27/2026", "Protean")
            }
        }
        nps = {
            "SM001001": nav_record("49.3817", "10/27/2026", "NPS Trust")
        }

        result = compare_nav_sources(protean, nps)

        self.assertEqual(result["shared_count"], 1)
        self.assertEqual(result["mismatches"], [])

    def test_empty_sources_are_supported(self):
        result = compare_nav_sources({}, {})

        self.assertEqual(
            result,
            {
                "shared_count": 0,
                "mismatches": [],
                "different_date_schemes": [],
            },
        )


class GroupRecordsByDateTests(unittest.TestCase):
    def test_groups_by_actual_date_and_prefers_protean_on_overlap(self):
        protean_same_date = nav_record("20.0000", "10/27/2026", "Protean")
        protean_older = nav_record("30.0000", "10/27/2026", "Protean")
        nps_same_date = nav_record("20.5000", "10/27/2026", "NPS Trust")
        nps_newer = nav_record("31.0000", "10/28/2026", "NPS Trust")
        nps_only = nav_record("40.0000", "10/28/2026", "NPS Trust")

        protean = {
            "requested-date-one": {
                "SM001001": protean_same_date,
                "SM001002": protean_older,
            }
        }
        nps = {
            "SM001001": nps_same_date,
            "SM001002": nps_newer,
            "SM001003": nps_only,
        }

        grouped = group_records_by_date(protean, nps)

        self.assertIs(grouped["10/27/2026"]["SM001001"], protean_same_date)
        self.assertIs(grouped["10/27/2026"]["SM001002"], protean_older)
        # NPS Trust is newer than Protean for SM001002, so it fills the gap
        self.assertIs(grouped["10/28/2026"]["SM001002"], nps_newer)
        self.assertIs(grouped["10/28/2026"]["SM001003"], nps_only)

    def test_nps_newer_than_protean_is_used_when_protean_lags(self):
        # Regression: Protean ZIP stuck at 11/19 while NPS Trust had 11/20
        protean_rec = nav_record("58.4660", "11/19/2026", "Protean")
        nps_rec = nav_record("58.9768", "11/20/2026", "NPS Trust")

        grouped = group_records_by_date(
            {"11/19/2026": {"SM001003": protean_rec}}, {"SM001003": nps_rec}
        )

        self.assertIs(grouped["11/19/2026"]["SM001003"], protean_rec)
        self.assertIs(grouped["11/20/2026"]["SM001003"], nps_rec)

    def test_nps_older_than_protean_is_ignored(self):
        protean_rec = nav_record("50.0000", "11/20/2026", "Protean")
        nps_rec = nav_record("49.0000", "11/19/2026", "NPS Trust")

        grouped = group_records_by_date(
            {"11/20/2026": {"SM001001": protean_rec}}, {"SM001001": nps_rec}
        )

        self.assertEqual(grouped, {"11/20/2026": {"SM001001": protean_rec}})

    def test_nps_is_used_as_fallback_when_protean_is_unavailable(self):
        nps_record = nav_record("40.0000", "10/28/2026", "NPS Trust")

        grouped = group_records_by_date({}, {"SM001003": nps_record})

        self.assertIs(grouped["10/28/2026"]["SM001003"], nps_record)

    def test_records_without_dates_are_ignored(self):
        protean = {"unknown": {"SM001001": nav_record("10.0", "", "Protean")}}
        nps = {"SM001002": nav_record("20.0", "", "NPS Trust")}

        self.assertEqual(group_records_by_date(protean, nps), {})



class FilterRowsForSchemeTests(unittest.TestCase):
    def test_drops_rows_for_remapped_direct_scheme(self):
        # Requesting old POP code SM001003 returns SM001025 (DIRECT) rows too
        df = pd.DataFrame({
            "DATE OF NAV": ["2026-11-18", "2026-03-31"],
            "SCHEME ID": ["SM001025", "SM001003"],
            "NAV VALUE": [57.8954, 51.6234],
        })

        result = filter_rows_for_scheme(df, "SM001003")

        self.assertEqual(list(result["SCHEME ID"]), ["SM001003"])

    def test_without_scheme_id_column_returns_unchanged(self):
        df = pd.DataFrame({"DATE OF NAV": ["2026-11-18"], "NAV VALUE": [1.0]})

        self.assertIs(filter_rows_for_scheme(df, "SM001003"), df)

if __name__ == "__main__":
    unittest.main()
