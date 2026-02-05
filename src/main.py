def categorize_funds(funds):
    categorized = {
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }
    
    for fund in funds:
        if fund['type'] == 'Tax Saver':
            categorized['Tax Saver'].append(fund)
        elif fund['type'] == 'Central Government':
            categorized['Central Government'].append(fund)
        elif fund['type'] == 'State Government':
            categorized['State Government'].append(fund)
        else:
            categorized['Others'].append(fund)
    
    return categorized