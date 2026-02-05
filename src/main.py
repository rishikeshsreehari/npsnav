import json

def load_funds():
    with open('data/funding.json') as f:
        return json.load(f)

def categorize_fund(fund):
    if "Tax Saver" in fund['name']:
        return 'Tax Saver'
    elif "Central Government" in fund['name']:
        return 'Central Government'
    elif "State Government" in fund['name']:
        return 'State Government'
    # Add more conditions here for better categorization
    return 'Others'

def build_fund_segments():
    funds = load_funds()
    segments = {'Tax Saver': [], 'Central Government': [], 'State Government': [], 'Others': []}
    for fund in funds:
        category = categorize_fund(fund)
        segments[category].append(fund)
    return segments

if __name__ == "__main__":
    segments = build_fund_segments()
    # Code to display segments on the home page