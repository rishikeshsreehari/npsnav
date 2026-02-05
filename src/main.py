def categorize_schemes(schemes):
    categorized = {
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }

    for scheme in schemes:
        if 'Tax Saver' in scheme.name:
            categorized['Tax Saver'].append(scheme)
        elif 'Central Government' in scheme.name:
            categorized['Central Government'].append(scheme)
        elif 'State Government' in scheme.name:
            categorized['State Government'].append(scheme)
        else:
            categorized['Others'].append(scheme)

    return categorized