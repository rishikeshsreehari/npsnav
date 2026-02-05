def categorize_funds(fund):
    if "Tax Saver" in fund.name:
        return "Tax Saver"
    elif "Central Government" in fund.name:
        return "Central Government"
    elif "State Government" in fund.name:
        return "State Government"
    # existing conditions...
    return "Others"  # default category