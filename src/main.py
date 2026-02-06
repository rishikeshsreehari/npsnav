# Main categorization logic for NPS funds

# Existing categories
categories = {
    "Equity": [],
    "Corporate Bond": [],
    "Government Bond": [],
    "Mixed": [],
    "Others": []
}

# New categories to improve segmentation
tax_saver_funds = []
central_gov_funds = []
state_gov_funds = []

# Process each fund
for fund in all_funds:
    if fund.is_tax_saver():
        tax_saver_funds.append(fund)
    elif fund.is_central_government():
        central_gov_funds.append(fund)
    elif fund.is_state_government():
        state_gov_funds.append(fund)
    elif fund.is_equity():
        categories["Equity"].append(fund)
    elif fund.is_corporate_bond():
        categories["Corporate Bond"].append(fund)
    elif fund.is_government_bond():
        categories["Government Bond"].append(fund)
    else:
        categories["Others"].append(fund)

# Add new categories to the main categories
categories["Tax Saver"] = tax_saver_funds
categories["Central Government"] = central_gov_funds
categories["State Government"] = state_gov_funds