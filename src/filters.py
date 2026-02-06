def improve_filters(funds):
    enhanced_filters = {
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }
    
    for fund in funds:
        if 'tax' in fund['name'].lower():
            enhanced_filters['Tax Saver'].append(fund)
        elif 'central' in fund['name'].lower():
            enhanced_filters['Central Government'].append(fund)
        elif 'state' in fund['name'].lower():
            enhanced_filters['State Government'].append(fund)
        else:
            enhanced_filters['Others'].append(fund)
    
    return enhanced_filters