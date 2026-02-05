import json

def categorize_funds(funds):
    categorized = {
        "Tax Saver": [],
        "Central Government": [],
        "State Government": [],
        "Others": []
    }
    
    for fund in funds:
        if fund['type'] == 'Tax Saver':
            categorized["Tax Saver"].append(fund)
        elif fund['type'] == 'Central Government':
            categorized["Central Government"].append(fund)
        elif fund['type'] == 'State Government':
            categorized["State Government"].append(fund)
        else:
            categorized["Others"].append(fund)
    
    return categorized

def build_site():
    with open('data/funds.json') as f:
        funds = json.load(f)
    
    categorized_funds = categorize_funds(funds)
    # Additional logic to build the site with categorized_funds

if __name__ == "__main__":
    build_site()