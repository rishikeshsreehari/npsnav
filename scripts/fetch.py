import requests
import zipfile
import os
from io import BytesIO
import json
from collections import OrderedDict
from datetime import datetime, timedelta

def download_and_extract_nav(date_str):
    url = f"https://npscra.nsdl.co.in/download/NAV_File_{date_str}.zip"
    response = requests.get(url)
    
    if response.status_code == 200:
        print(f"Successfully downloaded: {url}")
        
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            for file_name in zip_ref.namelist():
                if file_name.endswith('.out'):
                    zip_ref.extract(file_name, os.getcwd())
                    print(f"Extracted: {file_name}")
                    return file_name
        
        print("No .out file found in the ZIP archive.")
        return None
    elif response.status_code == 404:
        print(f"NAV file not available for the date: {date_str}. It might be a non-operational day.")
        return None
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")
        return None

def parse_out_file(file_name):
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

def save_to_root(data):
    root_file = "data/data.json"  # Overwrite the data.json file every day
    if os.path.exists(root_file):
        with open(root_file, 'r') as json_file:
            existing_data = json.load(json_file)
        existing_data.extend(data)
        data = existing_data

    with open(root_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"All data saved to {root_file}")

def update_scheme_json(data):
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
    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"Deleted {file_name}")

def get_last_date_in_data():
    root_file = "data/data.json"
    if os.path.exists(root_file):
        with open(root_file, 'r') as json_file:
            data = json.load(json_file)
            if data:
                last_entry = data[-1]
                last_date_str = last_entry['Date']
                return datetime.strptime(last_date_str, "%m/%d/%Y")
    return None

# Example usage
if __name__ == "__main__":
    # Get today's date
    today = datetime.now()
    
    # Get the last date from data.json
    last_date = get_last_date_in_data()
    
    if not last_date:
        # If no date found, start from a default date (e.g., 30th August 2024)
        last_date = datetime.strptime("30/08/2024", "%d/%m/%Y")

    # Iterate through each date from the last date + 1 day until today
    current_date = last_date + timedelta(days=1)
    while current_date <= today:
        date_str = current_date.strftime("%d%m%Y")
        print(f"Trying to fetch NAV data for {current_date.strftime('%d-%m-%Y')}...")  # Print statement added
        out_file = download_and_extract_nav(date_str)
        
        if out_file:
            nav_data = parse_out_file(out_file)
            save_to_root(nav_data)  # Save to data.json
            update_scheme_json(nav_data)
            clean_up(out_file)
        else:
            print(f"No NAV data available for {date_str}.")
        
        # Move to the next date
        current_date += timedelta(days=1)
