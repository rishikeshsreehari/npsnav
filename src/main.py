# src/main.py

def categorize_funds(all_funds):
    categorized_funds = {
        'Tax Saver': [],
        'Central Government': [],
        'State Government': [],
        'Others': []
    }
    
    for fund in all_funds:
        if 'tax' in fund['name'].lower():
            categorized_funds['Tax Saver'].append(fund)
        elif 'central' in fund['name'].lower():
            categorized_funds['Central Government'].append(fund)
        elif 'state' in fund['name'].lower():
            categorized_funds['State Government'].append(fund)
        else:
            categorized_funds['Others'].append(fund)

    return categorized_funds