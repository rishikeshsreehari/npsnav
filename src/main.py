def categorize_fund(scheme):
    if 'Tax Saver' in scheme:
        return 'Tax Saver'
    elif 'Central Government' in scheme:
        return 'Central Government'
    elif 'State Government' in scheme:
        return 'State Government'
    # Additional categories can be added here
    else:
        return 'Others'