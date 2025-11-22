import os
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

DATE_FORMAT = '%m/%d/%Y'

# Load the base data.json file
def load_base_data():
    with open('data/data.json', 'r') as file:
        return json.load(file)

# Load the historical NAV data for a specific scheme
def load_historical_data(scheme_code):
    file_path = os.path.join('data', f'{scheme_code}.json')
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

# Get the NAV for the strictly previous available date before the target date
def get_nav_for_previous_date(historical_data, target_date):
    target_datetime = datetime.strptime(target_date, DATE_FORMAT)
    sorted_dates = sorted(historical_data.keys(), key=lambda x: datetime.strptime(x, DATE_FORMAT), reverse=True)

    for date_str in sorted_dates:
        current_datetime = datetime.strptime(date_str, DATE_FORMAT)
        if current_datetime <= target_datetime:
            return date_str, historical_data[date_str]

    return None, None  # If no suitable date is found, return None

# Calculate the percentage return with two decimal places
def calculate_return(current_nav, past_nav):
    if current_nav and past_nav:
        return format((float(current_nav) - float(past_nav)) / float(past_nav) * 100, ".2f")
    return None

# Calculate annualized return (CAGR) with two decimal places
def calculate_annualized_return(current_nav, past_nav, years):
    if current_nav and past_nav:
        current_nav = float(current_nav)
        past_nav = float(past_nav)
        if past_nav != 0:  # Avoid division by zero
            cagr = (current_nav / past_nav) ** (1 / years) - 1
            return format(cagr * 100, ".2f")  # Convert to percentage and format to 2 decimal places
    return None

# Get the global latest date across all funds
def get_global_latest_date(base_data):
    """Find the most recent date across all funds"""
    latest = None
    for fund in base_data:
        fund_date = datetime.strptime(fund['Date'], DATE_FORMAT)
        if latest is None or fund_date > latest:
            latest = fund_date
    return latest

# Main function to calculate returns for a specific fund with period-based staleness detection
def calculate_returns_for_fund(fund, global_latest_date):
    scheme_code = fund['Scheme Code']
    scheme_name = fund['Scheme Name']
    print(f"Processing {scheme_name} ({scheme_code})...")

    historical_data = load_historical_data(scheme_code)
    
    if not historical_data:
        print(f"No historical data found for {scheme_code}. Skipping...")
        return
    
    latest_nav = fund['NAV']
    latest_date = fund['Date']
    latest_datetime = datetime.strptime(latest_date, DATE_FORMAT)
    
    # Calculate how many days behind this fund is from the global latest
    days_behind = (global_latest_date - latest_datetime).days
    
    # Define thresholds for each period (in days)
    # A period is only calculated if the fund's data is fresh enough
    period_thresholds = {
        '1D': 2,      # 1-day return needs data within 2 days
        '7D': 9,      # 7-day return needs data within 9 days
        '1M': 35,     # 1-month return needs data within 35 days
        '3M': 100,    # 3-month return needs data within 100 days
        '6M': 190,    # 6-month return needs data within 190 days
        '1Y': 380,    # 1-year return needs data within 380 days
        '3Y': None,   # 3-year return always calculated if data exists
        '5Y': None,   # 5-year return always calculated if data exists
    }
    
    # Calculate returns using the strictly previous available date
    one_day_date, one_day_nav = get_nav_for_previous_date(historical_data, (latest_datetime - relativedelta(days=1)).strftime(DATE_FORMAT))
    one_day_return = calculate_return(latest_nav, one_day_nav) if days_behind <= period_thresholds['1D'] else None
    
    seven_day_date, seven_day_nav = get_nav_for_previous_date(historical_data, (latest_datetime - relativedelta(days=7)).strftime(DATE_FORMAT))
    seven_day_return = calculate_return(latest_nav, seven_day_nav) if days_behind <= period_thresholds['7D'] else None
    
    one_month_date, one_month_nav = get_nav_for_previous_date(historical_data, (latest_datetime - relativedelta(months=1)).strftime(DATE_FORMAT))
    one_month_return = calculate_return(latest_nav, one_month_nav) if days_behind <= period_thresholds['1M'] else None
    
    three_month_date, three_month_nav = get_nav_for_previous_date(historical_data, (latest_datetime - relativedelta(months=3)).strftime(DATE_FORMAT))
    three_month_return = calculate_return(latest_nav, three_month_nav) if days_behind <= period_thresholds['3M'] else None
    
    six_month_date, six_month_nav = get_nav_for_previous_date(historical_data, (latest_datetime - relativedelta(months=6)).strftime(DATE_FORMAT))
    six_month_return = calculate_return(latest_nav, six_month_nav) if days_behind <= period_thresholds['6M'] else None
    
    one_year_date, one_year_nav = get_nav_for_previous_date(historical_data, (latest_datetime - relativedelta(years=1)).strftime(DATE_FORMAT))
    one_year_return = calculate_return(latest_nav, one_year_nav) if days_behind <= period_thresholds['1Y'] else None
    
    three_year_date, three_year_nav = get_nav_for_previous_date(historical_data, (latest_datetime - relativedelta(years=3)).strftime(DATE_FORMAT))
    three_year_return = calculate_annualized_return(latest_nav, three_year_nav, 3)  # Always calculate if data exists
    
    five_year_date, five_year_nav = get_nav_for_previous_date(historical_data, (latest_datetime - relativedelta(years=5)).strftime(DATE_FORMAT))
    five_year_return = calculate_annualized_return(latest_nav, five_year_nav, 5)  # Always calculate if data exists
    
    if days_behind > period_thresholds['1D']:
        print(f"  ⚠️  Data is {days_behind} days old - some short-term returns set to null")
    
    # Update the fund entry with calculated returns
    fund['1D'] = one_day_return
    fund['7D'] = seven_day_return
    fund['1M'] = one_month_return
    fund['3M'] = three_month_return
    fund['6M'] = six_month_return
    fund['1Y'] = one_year_return
    fund['3Y'] = three_year_return
    fund['5Y'] = five_year_return

# Save the updated data back to data.json
def save_updated_data(base_data):
    with open('data/data.json', 'w') as file:
        json.dump(base_data, file, indent=4)

# Main execution
if __name__ == "__main__":
    base_data = load_base_data()
    
    # Get the global latest date
    global_latest_date = get_global_latest_date(base_data)
    print(f"Global latest date: {global_latest_date.strftime(DATE_FORMAT)}")
    
    # Iterate over all funds and calculate returns for each
    for fund in base_data:
        calculate_returns_for_fund(fund, global_latest_date)
    
    save_updated_data(base_data)
    print("Returns calculated for all funds and data.json updated successfully.")