def categorize_funds(funds):
    categorized = {
        "Equity": [],
        "Corporate Bond": [],
        "Government Bond": [],
        "Tax Saver": [],
        "Central Government": [],
        "State Government": [],
        "Others": []
    }

    for fund in funds:
        if fund['type'] == 'Equity':
            categorized["Equity"].append(fund)
        elif fund['type'] == 'Corporate Bond':
            categorized["Corporate Bond"].append(fund)
        elif fund['type'] == 'Government Bond':
            categorized["Government Bond"].append(fund)
        elif fund['category'] == 'Tax Saver':
            categorized["Tax Saver"].append(fund)
        elif fund['category'] == 'Central Government':
            categorized["Central Government"].append(fund)
        elif fund['category'] == 'State Government':
            categorized["State Government"].append(fund)
        else:
            categorized["Others"].append(fund)

    return categorized