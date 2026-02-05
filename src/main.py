# Main script responsible for building the fund categories
# Enhanced segmentation logic to improve fund classification

def categorize_fund(fund):
    """Categorize funds based on scheme characteristics."""
    if fund['type'] == 'Tax Saver':
        return 'Tax Saver'
    elif fund['type'] == 'Central Government':
        return 'Central Government'
    elif fund['type'] == 'State Government':
        return 'State Government'
    # Add additional checks for other fund types as needed
    return 'Others'  # Default classification

def build_fund_data(funds):
    """Builds categorized fund data."""
    categorized_funds = {
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }
    for fund in funds:
        category = categorize_fund(fund)
        categorized_funds[category].append(fund)
    return categorized_funds