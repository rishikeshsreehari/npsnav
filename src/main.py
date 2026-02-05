def segment_funds(funds):
    """Segment funds into categories."""
    categorized_funds = {
        'Equity': [],
        'Corporate Debt': [],
        'Government Bonds': [],
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }

    for fund in funds:
        if 'Equity' in fund['type']:
            categorized_funds['Equity'].append(fund)
        elif 'Corporate Debt' in fund['type']:
            categorized_funds['Corporate Debt'].append(fund)
        elif 'Government' in fund['type']:
            if 'Central' in fund['type']:
                categorized_funds['Central Government'].append(fund)
            elif 'State' in fund['type']:
                categorized_funds['State Government'].append(fund)
            else:
                categorized_funds['Government Bonds'].append(fund)
        elif 'Tax Saver' in fund['type']:
            categorized_funds['Tax Saver'].append(fund)
        else:
            categorized_funds['Others'].append(fund)

    return categorized_funds