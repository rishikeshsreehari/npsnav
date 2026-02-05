# File content for src/main.py
# Existing code...

def categorize_fund(fund):
    # Existing categorization logic...
    
    # Improved categorization for specific fund types
    if "Tax Saver" in fund['name']:
        return "Tax Saver"
    elif "Central Government" in fund['name']:
        return "Central Government"
    elif "State Government" in fund['name']:
        return "State Government"
    # More conditions can be added as needed

    return "Others"  # Default category