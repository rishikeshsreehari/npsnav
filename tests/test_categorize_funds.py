import unittest
from src.main import categorize_funds

class TestCategorizeFunds(unittest.TestCase):
    def test_tax_saver(self):
        self.assertEqual(categorize_funds(Fund(name="Tax Saver Fund")), "Tax Saver")
    
    def test_central_government(self):
        self.assertEqual(categorize_funds(Fund(name="Central Government Fund")), "Central Government")
    
    def test_state_government(self):
        self.assertEqual(categorize_funds(Fund(name="State Government Fund")), "State Government")
    
    def test_default(self):
        self.assertEqual(categorize_funds(Fund(name="Other Fund")), "Others")

if __name__ == "__main__":
    unittest.main()