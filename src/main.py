def categorize_funds(funds):
    categories = {
        "Tax Saver": [],
        "Central Government": [],
        "State Government": [],
        "Others": []
    }

    for fund in funds:
        if fund['type'] == 'Tax Saver':
            categories["Tax Saver"].append(fund)
        elif fund['type'] == 'Central Government':
            categories["Central Government"].append(fund)
        elif fund['type'] == 'State Government':
            categories["State Government"].append(fund)
        else:
            categories["Others"].append(fund)

    return categories