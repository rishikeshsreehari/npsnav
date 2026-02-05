import json

def categorize_funds(fund):
    if fund['type'] == 'Tax Saver':
        return 'Tax Saver'
    elif fund['type'] == 'Central Government':
        return 'Central Government'
    elif fund['type'] == 'State Government':
        return 'State Government'
    else:
        return 'Others'

def build_fund_data():
    with open('data/funds.json') as f:
        funds = json.load(f)
    
    categorized_funds = {
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }
    
    for fund in funds:
        category = categorize_funds(fund)
        categorized_funds[category].append(fund)
    
    return categorized_funds

if __name__ == "__main__":
    fund_data = build_fund_data()
    # Logic to dump categorized data into output files