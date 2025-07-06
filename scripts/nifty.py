import json
import os
import requests
from datetime import datetime
from pathlib import Path

DATE_FORMAT = '%m/%d/%Y'  # Define the date format for consistency

def fetch_nifty_data():
    """Fetch Nifty data from the custom endpoint"""
    # Get the endpoint URL from environment variable (GitHub secret)
    endpoint_url = os.getenv('NIFTY_ENDPOINT_URL')
    
    if not endpoint_url:
        raise ValueError("NIFTY_ENDPOINT_URL environment variable not set. Please add it as a GitHub secret.")
    
    try:
        response = requests.get(endpoint_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to fetch data from endpoint: {e}")

def convert_date_format(date_str):
    """Convert date from DD-MM-YYYY to MM/DD/YYYY format"""
    try:
        # Parse the date from DD-MM-YYYY format
        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
        # Convert to MM/DD/YYYY format
        return date_obj.strftime(DATE_FORMAT)
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected DD-MM-YYYY format. Error: {e}")

def main():
    """Main function to fetch Nifty data and save/update it in JSON"""
    try:
        # Fetch data from the custom endpoint
        data = fetch_nifty_data()
        
        # Extract and validate data
        if 'pricecurrent' not in data or 'date' not in data:
            raise ValueError("Invalid response format. Expected 'pricecurrent' and 'date' fields.")
        
        closing_price = float(data['pricecurrent'])
        closing_price_formatted = "{:.2f}".format(closing_price)
        
        # Convert date format from DD-MM-YYYY to MM/DD/YYYY
        date_formatted = convert_date_format(data['date'])
        
        # Ensure data directory exists
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Load existing JSON data or initialize new dictionary
        json_file_path = data_dir / 'nifty.json'
        if json_file_path.exists():
            with json_file_path.open('r') as f:
                json_data = json.load(f)
        else:
            json_data = {}

        # Check if today's data exists and if it needs updating
        if date_formatted in json_data:
            if json_data[date_formatted] != closing_price_formatted:
                print(f"Updating Nifty 50 data for {date_formatted}: {json_data[date_formatted]} -> {closing_price_formatted}")
                json_data[date_formatted] = closing_price_formatted
            else:
                print(f"Data for {date_formatted} is already up-to-date.")
        else:
            print(f"Adding new data for {date_formatted}: {closing_price_formatted}")
            json_data[date_formatted] = closing_price_formatted

        # Sort the data by date in reverse order (newest date first)
        sorted_json_data = dict(
            sorted(json_data.items(), key=lambda x: datetime.strptime(x[0], DATE_FORMAT), reverse=True)
        )

        # Save the updated data back to the JSON file
        with json_file_path.open('w') as f:
            json.dump(sorted_json_data, f, indent=4)

        print(f"Nifty 50 closing price for {date_formatted}: {closing_price_formatted}")
        
        # Optional: Print previous close for reference
        if 'priceprevclose' in data:
            prev_close = float(data['priceprevclose'])
            change = closing_price - prev_close
            change_percent = (change / prev_close) * 100
            print(f"Previous close: {prev_close:.2f}, Change: {change:+.2f} ({change_percent:+.2f}%)")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()
