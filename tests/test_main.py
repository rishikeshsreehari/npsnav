import unittest
from src.main import categorize_funds

class TestCategorizeFunds(unittest.TestCase):
    def test_fund_categorization(self):
        funds = [
            {'type': 'Equity', 'category': 'General'},
            {'type': 'Corporate Bond', 'category': 'Tax Saver'},
            {'type': 'Government Bond', 'category': 'Central Government'},
            {'type': 'Equity', 'category': 'State Government'},
            {'type': 'Equity', 'category': 'Others'},
        ]
        categorized = categorize_funds(funds)
        self.assertEqual(len(categorized["Equity"]), 3)
        self.assertEqual(len(categorized["Corporate Bond"]), 1)
        self.assertEqual(len(categorized["Government Bond"]), 1)
        self.assertEqual(len(categorized["Tax Saver"]), 1)
        self.assertEqual(len(categorized["Central Government"]), 1)
        self.assertEqual(len(categorized["State Government"]), 1)
        self.assertEqual(len(categorized["Others"]), 1)

if __name__ == '__main__':
    unittest.main()