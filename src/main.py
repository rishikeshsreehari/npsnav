def categorize_funds(fund):
    if fund['type'] == 'Tax Saver':
        return 'Tax Saver'
    elif fund['type'] in ['Central Government', 'State Government']:
        return 'Government'
    # Add more categories as needed
    else:
        return 'Others'

def build_funds():
    funds = fetch_funds()
    categorized_funds = {
        'Tax Saver': [],
        'Government': [],
        'Others': []
    }
    for fund in funds:
        category = categorize_funds(fund)
        categorized_funds[category].append(fund)
    return categorized_funds