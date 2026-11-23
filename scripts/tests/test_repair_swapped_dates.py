import unittest

from scripts.repair_swapped_dates import plan_repairs


class PlanRepairsTests(unittest.TestCase):
    def setUp(self):
        # 11/04/2016 holds 11 Apr's NAV (real trading day); 10/02/2020 is a holiday copy
        self.history = {
            "04/11/2016": "16.7164", "11/03/2016": "19.1222", "11/04/2016": "16.7164", "11/07/2016": "19.1495",
            "02/10/2020": "26.2343", "10/01/2020": "24.9961", "10/02/2020": "26.2343", "10/05/2020": "25.1617",
        }
        self.dates = ["11/04/2016", "10/02/2020"]
        self.flagged = {"SM001003": {"11/04/2016", "10/02/2020"}}

    def test_replace_when_source_has_date_and_delete_non_nav_date(self):
        nps = {"SM001003": {"11/03/2016": "19.1222", "11/04/2016": "18.991", "11/07/2016": "19.1495",
                            "10/01/2020": "24.9961", "10/05/2020": "25.1617"}}

        plan = plan_repairs({"SM001003": self.history}, nps, self.dates, self.flagged)

        self.assertEqual(sorted(plan["SM001003"]), [
            ("10/02/2020", "delete", "26.2343", None),
            ("11/04/2016", "replace", "16.7164", "18.991"),
        ])

    def test_flagged_copy_without_source_is_deleted(self):
        plan = plan_repairs({"SM006001": self.history}, {"SM006001": None, "SM001001": {"11/04/2016": "20.0"}},
                            self.dates, {"SM006001": {"11/04/2016"}})

        self.assertIn(("11/04/2016", "delete", "16.7164", None), plan["SM006001"])

    def test_matching_source_value_is_left_alone(self):
        history = {"04/11/2016": "10.0", "11/04/2016": "10.0"}
        nps = {"SM002010": {"11/04/2016": "10.0"}}

        plan = plan_repairs({"SM002010": history}, nps, ["11/04/2016"], {})

        self.assertEqual(dict(plan), {})


if __name__ == "__main__":
    unittest.main()
