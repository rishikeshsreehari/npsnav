def categorize_fund(fund):
    """Categorizes a fund based on its attributes."""
    if "Tax Saver" in fund['name']:
        return "Tax Saver"
    elif "Central Government" in fund['name']:
        return "Central Government"
    elif "State Government" in fund['name']:
        return "State Government"
    # Add additional conditions for other categories as needed
    return "Others"

def build_fund_data(funds):
    """Builds fund data with improved categorization."""
    categorized_funds = {
        "Tax Saver": [],
        "Central Government": [],
        "State Government": [],
        "Others": [],
    }
    for fund in funds:
        category = categorize_fund(fund)
        categorized_funds[category].append(fund)
    return categorized_funds