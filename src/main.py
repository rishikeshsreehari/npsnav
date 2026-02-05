# Existing imports and code

def categorize_fund(fund):
    if fund['type'] == 'Tax Saver':
        return 'Tax Saver'
    elif fund['type'] == 'Central Government':
        return 'Central Government'
    elif fund['type'] == 'State Government':
        return 'State Government'
    # Add other specific types here
    else:
        return 'Others'

def build_fund_list():
    funds = fetch_funds()
    categorized_funds = {}
    for fund in funds:
        category = categorize_fund(fund)
        if category not in categorized_funds:
            categorized_funds[category] = []
        categorized_funds[category].append(fund)

    return categorized_funds

# Continue with existing logic to render the homepage