def categorize_fund(scheme_name):
    """Categorize funds based on scheme name."""
    if 'Tax Saver' in scheme_name:
        return 'Tax Saver'
    elif 'Central Government' in scheme_name:
        return 'Central Government'
    elif 'State Government' in scheme_name:
        return 'State Government'
    # Add more conditions as needed
    else:
        return 'Others'