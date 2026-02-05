def categorize_funds(fund):
    if fund['type'] == 'Tax Saver':
        return 'Tax Saver'
    elif fund['type'] == 'Central Government':
        return 'Central Government'
    elif fund['type'] == 'State Government':
        return 'State Government'
    else:
        return 'Others'

def build_fund_categories(funds):
    categories = {
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }
    
    for fund in funds:
        category = categorize_funds(fund)
        categories[category].append(fund)
    
    return categories