import os
import requests
import json
from datetime import datetime
from pathlib import Path

# Set the base URL for your Cloudflare Worker
WORKER_BASE_URL = 'https://npsnav.rishikeshsreehari.workers.dev'

# Define date format used in the database
DATE_FORMAT = '%Y-%m-%d'

# Get the authorization token from the environment
AUTH_TOKEN = os.getenv('AUTH_TOKEN_NPSNAV_DBWORKER')

# Headers including the authorization token
headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}

# List of fund IDs to ignore
ignore_fund_ids = [
    'SM006001', 'SM006002', 'SM006003', 'SM006004', 'SM006005', 'SM006006', 'SM006007', 'SM006008', 'SM006009',
    'SM009001', 'SM009002', 'SM009003', 'SM009004', 'SM009005', 'SM009006', 'SM009007'
]

def reformat_date(date_str):
    """Convert date from MM/DD/YYYY to YYYY-MM-DD format."""
    return datetime.strptime(date_str, '%m/%d/%Y').strftime(DATE_FORMAT)

def get_latest_date_for_fund(fund_id):
    """Fetch the latest NAV date for a given fund using the Cloudflare Worker."""
    response = requests.get(f"{WORKER_BASE_URL}/latest-fund", params={'fund_id': fund_id})
    if response.ok:
        result = response.json()
        return datetime.strptime(result['date'], DATE_FORMAT).date() if result['date'] else None
    else:
        raise Exception(f"Failed to fetch latest date for fund {fund_id}")

def get_latest_nifty_date():
    """Fetch the latest NAV date for Nifty using the Cloudflare Worker."""
    response = requests.get(f"{WORKER_BASE_URL}/latest-nifty")
    if response.ok:
        result = response.json()
        return datetime.strptime(result['date'], DATE_FORMAT).date() if result['date'] else None
    else:
        raise Exception("Failed to fetch latest Nifty date")

def update_fund_nav_data(fund_id, new_data):
    """Update NAV data for a specific fund in D1 database via Cloudflare Worker."""
    for date, nav in new_data.items():
        # Reformat date to match the database format
        formatted_date = reformat_date(date)
        data = {'fund_id': fund_id, 'date': formatted_date, 'nav': nav}
        response = requests.post(f"{WORKER_BASE_URL}/update-fund", json=data, headers=headers)
        if not response.ok:
            raise Exception(f"Failed to update NAV for fund {fund_id} on {formatted_date}")

def update_nifty_data(new_data):
    """Update Nifty NAV data in D1 database via Cloudflare Worker."""
    for date, nav in new_data.items():
        # Reformat date to match the database format
        formatted_date = reformat_date(date)
        data = {'date': formatted_date, 'nav': nav}
        response = requests.post(f"{WORKER_BASE_URL}/update-nifty", json=data, headers=headers)
        if not response.ok:
            raise Exception(f"Failed to update Nifty data for {formatted_date}")

def load_json_data(file_path):
    """Load data from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def update_fund_data(data_dir='data'):
    """Update NAV data for each fund from its JSON file."""
    for json_file in Path(data_dir).glob("*.json"):
        # Skip specific files
        if json_file.stem in ['data', 'nifty']:
            continue

        fund_id = json_file.stem
        # Skip ignored fund IDs
        if fund_id in ignore_fund_ids:
            print(f"Skipping fund {fund_id} as it's in the ignore list.")
            continue

        print(f"Processing fund {fund_id}...")
        latest_date = get_latest_date_for_fund(fund_id)
        
        fund_data = load_json_data(json_file)
        
        # Filter new data only (dates after the latest date)
        new_data = {
            date: nav for date, nav in fund_data.items()
            if datetime.strptime(reformat_date(date), DATE_FORMAT).date() > (latest_date or datetime.min.date())
        }

        if new_data:
            update_fund_nav_data(fund_id, new_data)
            latest_update_date = max(datetime.strptime(reformat_date(date), DATE_FORMAT).date() for date in new_data.keys())
            print(f"Updated NAV for {fund_id} with {len(new_data)} new records up to {latest_update_date}.")
        else:
            print(f"No new data for {fund_id}.")

def update_nifty_data_from_json(nifty_json_path='data/nifty.json'):
    """Update Nifty data from the JSON file."""
    latest_date = get_latest_nifty_date()
    
    nifty_data = load_json_data(nifty_json_path)
    
    # Filter new data only
    new_data = {
        date: nav for date, nav in nifty_data.items()
        if datetime.strptime(reformat_date(date), DATE_FORMAT).date() > (latest_date or datetime.min.date())
    }

    if new_data:
        update_nifty_data(new_data)
        latest_update_date = max(datetime.strptime(reformat_date(date), DATE_FORMAT).date() for date in new_data.keys())
        print(f"Updated Nifty values with {len(new_data)} new records up to {latest_update_date}.")
    else:
        print("No new data for Nifty.")

def main():
    try:
        update_fund_data('data')  # Directory containing JSON data for funds
        update_nifty_data_from_json('data/nifty.json')  # Path to Nifty JSON file
        print("Database updated successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
