import json

def categorize_funds(funds):
    categorized = {
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }
    
    for fund in funds:
        if fund['type'] == 'Tax Saver':
            categorized['Tax Saver'].append(fund)
        elif fund['type'] == 'Central Government':
            categorized['Central Government'].append(fund)
        elif fund['type'] == 'State Government':
            categorized['State Government'].append(fund)
        else:
            categorized['Others'].append(fund)
    
    return categorized

def load_funds(filepath):
    with open(filepath) as f:
        return json.load(f)

def main():
    funds = load_funds('data/funds.json')
    categorized_funds = categorize_funds(funds)
    # More logic to display the categorized funds on the home page

if __name__ == "__main__":
    main()