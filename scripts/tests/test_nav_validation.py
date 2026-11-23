import unittest

import pandas as pd

import glob
import json
import os
from datetime import datetime

from scripts.nav_validation import (
    find_swapped_date_copies,
    parse_source_date,
    apply_protean_names,
    choose_scheme_name,
    parse_protean_line,
    pick_protean_member,
    clean_cell,
    compare_nav_sources,
    filter_rows_for_scheme,
    group_records_by_date,
    merge_latest_records,
    parse_nav,
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


class BlankCellTests(unittest.TestCase):
    def test_clean_cell_maps_blanks_to_empty(self):
        for value in (None, float("nan"), "", "  ", "nan", "NaN", "None"):
            self.assertEqual(clean_cell(value), "", repr(value))

    def test_clean_cell_keeps_real_values(self):
        self.assertEqual(clean_cell("  SM001003 "), "SM001003")
        self.assertEqual(clean_cell(12.5), "12.5")

    def test_parse_nav_rejects_blank_and_invalid(self):
        for value in (None, float("nan"), "", "nan", "abc", "0", "-1.5", "inf"):
            self.assertIsNone(parse_nav(value), repr(value))

    def test_parse_nav_normalizes_valid_values(self):
        self.assertEqual(parse_nav(" 49.74990 "), "49.7499")
        self.assertEqual(parse_nav(57.8954), "57.8954")

    def test_blank_dump_rows_from_pandas_are_rejected(self):
        df = pd.read_csv(
            __import__("io").StringIO("SCHEME ID\tNAV VALUE\nSM001003\t\n\t12.5\n"),
            sep="\t",
        )
        rows = [(clean_cell(r["SCHEME ID"]), parse_nav(r["NAV VALUE"])) for _, r in df.iterrows()]
        self.assertEqual(rows, [("SM001003", None), ("", "12.5")])


def latest_record(code, date, nav, name="X"):
    return {"Date": date, "PFM Code": "PFM" + code[2:5], "Scheme Code": code,
            "Scheme Name": name, "PFM Name": name, "NAV": nav}


class MergeLatestRecordsTests(unittest.TestCase):
    def test_same_date_correction_replaces_stale_nav(self):
        existing = [latest_record("SM001003", "11/20/2026", "50.1")]
        new = [latest_record("SM001003", "11/20/2026", "50.2")]

        merged = merge_latest_records(existing, new)

        self.assertEqual([r["NAV"] for r in merged], ["50.2"])

    def test_older_new_record_does_not_replace_latest(self):
        existing = [latest_record("SM001003", "11/20/2026", "50.1")]
        new = [latest_record("SM001003", "11/18/2026", "49.0")]

        merged = merge_latest_records(existing, new)

        self.assertEqual([(r["Date"], r["NAV"]) for r in merged], [("11/20/2026", "50.1")])

    def test_names_are_not_taken_from_new_records(self):
        existing = [latest_record("SM001003", "11/19/2026", "50.0", name="CANONICAL")]
        new = [latest_record("SM001003", "11/20/2026", "50.1", name="FROM SOURCE")]

        merged = merge_latest_records(existing, new)[0]

        self.assertEqual((merged["Date"], merged["NAV"]), ("11/20/2026", "50.1"))
        self.assertEqual((merged["Scheme Name"], merged["PFM Name"]), ("CANONICAL", "CANONICAL"))

    def test_does_not_mutate_inputs(self):
        existing = [latest_record("SM001003", "11/19/2026", "50.0")]
        merge_latest_records(existing, [latest_record("SM001003", "11/20/2026", "50.1")])

        self.assertEqual(existing[0]["NAV"], "50.0")

    def test_newer_date_wins_and_untouched_schemes_are_kept(self):
        existing = [latest_record("SM001003", "11/19/2026", "50.0"),
                    latest_record("SM002003", "11/19/2026", "70.0")]
        new = [latest_record("SM001003", "11/18/2026", "49.0"),
               latest_record("SM001003", "11/20/2026", "50.1")]

        merged = {r["Scheme Code"]: r for r in merge_latest_records(existing, new)}

        self.assertEqual(merged["SM001003"]["NAV"], "50.1")
        self.assertEqual(merged["SM002003"]["NAV"], "70.0")
        self.assertEqual(len(merged), 2)


class ProteanParsingTests(unittest.TestCase):
    def test_pick_member_skips_macosx_junk(self):
        names = ["__MACOSX/._NAV_File_19112026.out", "NAV_File_19112026.out"]
        self.assertEqual(pick_protean_member(names), "NAV_File_19112026.out")
        self.assertIsNone(pick_protean_member(["__MACOSX/._NAV_File_19112026.out"]))

    def test_parse_standard_line(self):
        line = "11/19/2026,PFM001,SBI PENSION FUNDS PRIVATE LIMITED,SM001005,SBI PENSION FUND SCHEME G - TIER I POP,41.9297"
        self.assertEqual(parse_protean_line(line), {
            "code": "SM001005", "nav": "41.9297", "date": "11/19/2026",
            "pfm_name": "SBI PENSION FUNDS PRIVATE LIMITED",
            "scheme_name": "SBI PENSION FUND SCHEME G - TIER I POP",
        })

    def test_commas_in_names_do_not_drop_the_line(self):
        line = "11/19/2026,PFM001,SBI PENSION FUNDS, PRIVATE LIMITED,SM001005,SCHEME G, TIER I POP,41.9297\n"
        record = parse_protean_line(line)
        self.assertEqual(record["code"], "SM001005")
        self.assertEqual(record["nav"], "41.9297")
        self.assertEqual(record["pfm_name"], "SBI PENSION FUNDS, PRIVATE LIMITED")
        self.assertEqual(record["scheme_name"], "SCHEME G, TIER I POP")

    def test_malformed_lines_are_rejected(self):
        for line in (
            "",
            "DATE,PFM,PFM NAME,SCHEME ID,SCHEME NAME,NAV",
            "11/19/2026,PFM001,SBI,SM001005,SCHEME G,",
            "2026-11-19,PFM001,SBI,SM001005,SCHEME G,41.9",
            "11/19/2026,PFM001,SBI,NOTACODE,SCHEME G,41.9",
        ):
            self.assertIsNone(parse_protean_line(line), line)


class CanonicalNameTests(unittest.TestCase):
    def test_protean_name_wins(self):
        self.assertEqual(
            choose_scheme_name("SBI SCHEME E - TIER I POP", "SBI SCHEME E - TIER I", "SBI SCHEME E - TIER I"),
            "SBI SCHEME E - TIER I POP",
        )

    def test_tier_guard_keeps_tiered_name(self):
        protean = "ICICI PF NPS BALANCED ADVANTAGE FUND"
        tiered = "NPS TRUST A/C - ICICI PF NPS BALANCED ADVANTAGE FUND - TIER I"
        self.assertEqual(choose_scheme_name(protean, tiered, None), tiered)
        self.assertEqual(choose_scheme_name(protean, protean, tiered), tiered)

    def test_untiered_schemes_still_take_protean_name(self):
        self.assertEqual(
            choose_scheme_name("SBI SCHEME - CENTRAL GOVT", "Old name", "Dump name"),
            "SBI SCHEME - CENTRAL GOVT",
        )

    def test_missing_protean_name_keeps_current(self):
        self.assertEqual(choose_scheme_name("", "Current", "Dump"), "Current")

    def test_apply_updates_only_schemes_in_protean(self):
        records = [
            latest_record("SM001003", "11/20/2026", "50.1", name="SBI SCHEME E - TIER I"),
            latest_record("SM012001", "04/17/2025", "30.0", name="MAX LIFE SCHEME E - TIER I"),
        ]
        protean = {"SM001003": {"scheme_name": "SBI SCHEME E - TIER I POP", "pfm_name": "SBI PENSION FUNDS PRIVATE LIMITED"}}

        changes = apply_protean_names(records, protean)

        self.assertEqual(records[0]["Scheme Name"], "SBI SCHEME E - TIER I POP")
        self.assertEqual(records[0]["PFM Name"], "SBI PENSION FUNDS PRIVATE LIMITED")
        self.assertEqual(records[1]["Scheme Name"], "MAX LIFE SCHEME E - TIER I")
        self.assertEqual(len(changes), 2)
        self.assertEqual(apply_protean_names(records, protean), [])


class SourceDateTests(unittest.TestCase):
    def test_unambiguous_formats(self):
        self.assertEqual(parse_source_date("2025-06-04"), datetime(2025, 6, 4))
        self.assertEqual(parse_source_date("04-06-2025"), datetime(2025, 6, 4))  # dashed = day-first
        self.assertEqual(parse_source_date("13/06/2025"), datetime(2025, 6, 13))
        self.assertEqual(parse_source_date("06/13/2025"), datetime(2025, 6, 13))
        self.assertEqual(parse_source_date("05/05/2025"), datetime(2025, 5, 5))
        self.assertEqual(parse_source_date(datetime(2025, 6, 4)), datetime(2025, 6, 4))

    def test_ambiguous_slashed_dates_are_rejected(self):
        # 04/06/2025 could be 4 Jun or 6 Apr: guessing is how NAVs got stored under swapped dates
        self.assertIsNone(parse_source_date("04/06/2025"))
        self.assertIsNone(parse_source_date("11/04/2016"))

    def test_blank_and_header_cells(self):
        for value in (None, float("nan"), "", "DATE OF NAV", "not a date", "31/31/2025"):
            self.assertIsNone(parse_source_date(value), repr(value))


class SwappedDateCopyTests(unittest.TestCase):
    def test_spike_copy_on_trading_day_is_flagged(self):
        history = {"04/11/2016": "16.7164", "04/12/2016": "16.8153",
                   "11/03/2016": "19.1222", "11/04/2016": "16.7164", "11/07/2016": "19.1495"}
        self.assertEqual(find_swapped_date_copies(history), ["11/04/2016"])

    def test_weekend_copy_is_flagged(self):
        # 04/06/2025 is a Sunday holding 4 Jun's NAV
        history = {"04/04/2025": "51.2", "04/06/2025": "54.8799", "04/07/2025": "49.8",
                   "06/04/2025": "54.8799", "06/05/2025": "55.0"}
        self.assertEqual(find_swapped_date_copies(history), ["04/06/2025"])

    def test_flat_navs_are_not_flagged(self):
        history = {"07/02/2009": "10.0", "07/03/2009": "10.0", "07/06/2009": "10.0", "03/07/2009": "10.0"}
        self.assertEqual(find_swapped_date_copies(history), [])

    def test_genuine_values_are_not_flagged(self):
        history = {"11/03/2016": "19.1222", "11/04/2016": "18.991", "11/07/2016": "19.1495",
                   "04/11/2016": "16.7164"}
        self.assertEqual(find_swapped_date_copies(history), [])


class StoredHistoryIntegrityTests(unittest.TestCase):
    """Guards the committed data/SM*.json files against swapped-date copies coming back."""

    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

    def test_no_swapped_date_copies_in_stored_history(self):
        files = sorted(glob.glob(os.path.join(self.DATA_DIR, "SM*.json")))
        if not files:
            self.skipTest("no scheme files present")
        offenders = {}
        for path in files:
            with open(path) as f:
                flagged = find_swapped_date_copies(json.load(f))
            if flagged:
                offenders[os.path.basename(path)] = flagged
        self.assertEqual(offenders, {}, "run scripts/repair_swapped_dates.py")


if __name__ == "__main__":
    unittest.main()
