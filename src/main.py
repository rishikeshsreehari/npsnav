def categorize_funds(funds):
    categorized_funds = {
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }

    for fund in funds:
        if fund['type'] == 'Tax Saver':
            categorized_funds['Tax Saver'].append(fund)
        elif fund['type'] == 'Central Government':
            categorized_funds['Central Government'].append(fund)
        elif fund['type'] == 'State Government':
            categorized_funds['State Government'].append(fund)
        else:
            categorized_funds['Others'].append(fund)

    return categorized_funds