def categorize_scheme(scheme_code):
    # Define specific categories for proper filtering
    if scheme_code.startswith("SM") or scheme_code.startswith("CG"):
        return "Central Government"
    elif scheme_code.startswith("ST"):
        return "State Government"
    elif scheme_code.startswith("TS"):
        return "Tax Saver"
    else:
        return "Others"

def build_fund_data():
    # Existing logic to fetch and process funds
    fund_data = fetch_funds()
    categorized_funds = {}
    
    for fund in fund_data:
        category = categorize_scheme(fund['scheme_code'])
        if category not in categorized_funds:
            categorized_funds[category] = []
        categorized_funds[category].append(fund)
    
    return categorized_funds