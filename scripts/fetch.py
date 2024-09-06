import requests
import zipfile
import os
from io import BytesIO
import json
from collections import OrderedDict
from datetime import datetime, timedelta

def download_and_extract_nav(date_str, url_variations):
    """
    Attempt to download and extract the NAV data for a given date using multiple URL variations.
    Returns the extracted file name if successful, otherwise returns None.
    """
    for variation in url_variations:
        url = variation.format(date_str=date_str)
        print(f"Trying URL: {url}")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            print(f"Successfully downloaded: {url}")
            with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                for file_name in zip_ref.namelist():
                    if file_name.endswith('.out'):
                        zip_ref.extract(file_name, os.getcwd())
                        print(f"Extracted: {file_name}")
                        return file_name  # Return the extracted file name once successful
        
        elif response.status_code == 404:
            print(f"NAV file not available at {url}. Trying next variation.")
        else:
            print(f"Failed to download from {url}. Status code: {response.status_code}")
    
    return None  # If no variation worked, return None

def parse_out_file(file_name):
    """Parse the .out file and extract the NAV data."""
    data_list = []
    with open(file_name, 'r') as file:
        for line in file:
            columns = line.strip().split(',')
            if len(columns) == 6:
                scheme_data = {
                    "Date": columns[0],
                    "PFM Code": columns[1],
                    "PFM Name": columns[2],
                    "Scheme Code": columns[3],
                    "Scheme Name": columns[4],
                    "NAV": columns[5]
                }
                data_list.append(scheme_data)
    return data_list

def save_latest_data(new_data):
    """Save the latest NAV data to data.json, ensuring only the most recent NAV for each scheme is retained."""
    root_file = "data/data.json"
    os.makedirs(os.path.dirname(root_file), exist_ok=True)  # Ensure the data directory exists
    
    # Load existing data
    existing_data = []
    if os.path.exists(root_file):
        with open(root_file, 'r') as json_file:
            existing_data = json.load(json_file)
    
    # Combine existing and new data
    all_data = existing_data + new_data
    
    # Create a dictionary to store the latest record for each unique fund
    latest_records = {}
    
    for record in all_data:
        key = (record["PFM Code"], record["Scheme Code"])
        if key not in latest_records or datetime.strptime(record["Date"], "%m/%d/%Y") > datetime.strptime(latest_records[key]["Date"], "%m/%d/%Y"):
            latest_records[key] = record
    
    # Convert the dictionary values back to a list
    latest_data = list(latest_records.values())
    
    with open(root_file, 'w') as json_file:  # 'w' mode overwrites the file
        json.dump(latest_data, json_file, indent=4)
    print(f"Latest data saved to {root_file}")

def update_scheme_json(data):
    """Update individual JSON files for each scheme with the latest NAV data."""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    for scheme in data:
        scheme_code = scheme["Scheme Code"]
        scheme_file = os.path.join('data', f"{scheme_code}.json")
        
        if os.path.exists(scheme_file):
            with open(scheme_file, 'r') as f:
                scheme_data = json.load(f, object_pairs_hook=OrderedDict)
        else:
            scheme_data = OrderedDict()

        # Add or overwrite the NAV for the specific date
        scheme_data[scheme["Date"]] = scheme["NAV"]

        # Sort the dictionary by date (descending) and update
        sorted_scheme_data = OrderedDict(
            sorted(scheme_data.items(), key=lambda x: datetime.strptime(x[0], '%m/%d/%Y'), reverse=True)
        )

        with open(scheme_file, 'w') as f:
            json.dump(sorted_scheme_data, f, indent=4)
        print(f"Updated {scheme_file}")

def clean_up(file_name):
    """Delete the extracted .out file to clean up."""
    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"Deleted {file_name}")

def get_last_date_in_data():
    """Fetch the last available date from data.json to resume fetching from the correct point."""
    root_file = "data/data.json"
    if os.path.exists(root_file):
        with open(root_file, 'r') as json_file:
            data = json.load(json_file)
            if data:
                last_date = max(datetime.strptime(entry['Date'], "%m/%d/%Y") for entry in data)
                return last_date
    return None

if __name__ == "__main__":
    # Define the different case variations of the URL
    url_variations = [
        "https://npscra.nsdl.co.in/download/NAV_File_{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV_FILE_{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV_file_{date_str}.zip",
        # Add more variations if necessary
    ]
    
    # Get the last date from data.json or start from a default date
    last_date = get_last_date_in_data()
    today = datetime.now()
    
    if not last_date:
        last_date = datetime.strptime("30/08/2024", "%d/%m/%Y")  # Default start date

    all_nav_data = []  # This will hold the new data we're going to save

    # Start from the day after the last date
    current_date = last_date + timedelta(days=1)
    while current_date <= today:
        date_str = current_date.strftime("%d%m%Y")
        print(f"Trying to fetch NAV data for {current_date.strftime('%d-%m-%Y')}...")
        
        # Try to download and extract the file using the URL variations
        out_file = download_and_extract_nav(date_str, url_variations)
        
        if out_file:
            nav_data = parse_out_file(out_file)
            all_nav_data.extend(nav_data)  # Add this day's data to our new dataset
            update_scheme_json(nav_data)
            clean_up(out_file)  # Clean up the .out file
        else:
            print(f"No NAV data available for {current_date.strftime('%d-%m-%Y')}.")
        
        current_date += timedelta(days=1)
    
    # Only update data.json if new data is available
    if all_nav_data:
        save_latest_data(all_nav_data)
        print(f"Script completed. Total new records saved: {len(all_nav_data)}")
    else:
        print("No new data available. Existing data.json remains unchanged.")
