import unittest
from main import categorize_funds

class TestCategorizeFunds(unittest.TestCase):
    def test_fund_categorization(self):
        funds = [
            {'name': 'Fund A', 'type': 'Equity'},
            {'name': 'Fund B', 'type': 'Debt'},
            {'name': 'Fund C', 'type': 'Tax Saver'},
            {'name': 'Fund D', 'type': 'Central Government'},
            {'name': 'Fund E', 'type': 'State Government'},
            {'name': 'Fund F', 'type': 'Unknown'}
        ]
        
        categorized = categorize_funds(funds)
        self.assertEqual(len(categorized['Equity']), 1)
        self.assertEqual(len(categorized['Debt']), 1)
        self.assertEqual(len(categorized['Tax Saver']), 1)
        self.assertEqual(len(categorized['Central Government']), 1)
        self.assertEqual(len(categorized['State Government']), 1)
        self.assertEqual(len(categorized['Others']), 1)

if __name__ == '__main__':
    unittest.main()