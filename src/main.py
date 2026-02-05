# Existing import statements
import json

def categorize_funds(fund_list):
    categorized_funds = {
        "Tax Saver": [],
        "Central Government": [],
        "State Government": [],
        "Others": []
    }
    
    for fund in fund_list:
        if "Tax Saver" in fund["name"]:
            categorized_funds["Tax Saver"].append(fund)
        elif "Central" in fund["name"]:
            categorized_funds["Central Government"].append(fund)
        elif "State" in fund["name"]:
            categorized_funds["State Government"].append(fund)
        else:
            categorized_funds["Others"].append(fund)

    return categorized_funds

def main():
    # Load fund data from JSON or any other source
    with open('data/funds.json') as f:
        fund_list = json.load(f)

    categorized_funds = categorize_funds(fund_list)
    # Save or process categorized funds as needed