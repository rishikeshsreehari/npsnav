import requests
import zipfile
import os
import time
import random
from io import BytesIO
import json
from collections import OrderedDict
from datetime import datetime, timedelta
from fake_useragent import UserAgent

# Reuse the download and extraction functions
def download_and_extract_nav(date_str, user_agent):
    url = f"https://npscra.nsdl.co.in/download/NAV_File_{date_str}.zip"
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    
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

        # Sort the dictionary to keep the latest NAV at the top
        sorted_scheme_data = OrderedDict(sorted(scheme_data.items(), reverse=True))

        with open(scheme_file, 'w') as f:
            json.dump(sorted_scheme_data, f, indent=4)
        print(f"Updated {scheme_file}")

def clean_up(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"Deleted {file_name}")

# Initialize or load error log
def load_error_log():
    error_file = "error.json"
    if os.path.exists(error_file):
        with open(error_file, 'r') as f:
            return json.load(f)
    else:
        return []

def save_error_log(error_log):
    with open("error.json", 'w') as f:
        json.dump(error_log, f, indent=4)

# New logic to fetch historical data with anti-blocking techniques
def fetch_historical_data(start_date_str, end_date_str):
    ua = UserAgent()  # Initialize a user-agent generator
    start_date = datetime.strptime(start_date_str, "%d-%m-%Y")
    end_date = datetime.strptime(end_date_str, "%d-%m-%Y")
    
    current_date = start_date
    error_log = load_error_log()

    while current_date >= end_date:
        date_str = current_date.strftime("%d%m%Y")
        user_agent = ua.random  # Use a random user-agent for each request
        print(user_agent)
        
        try:
            out_file = download_and_extract_nav(date_str, user_agent)
            
            if out_file:
                nav_data = parse_out_file(out_file)
                update_scheme_json(nav_data)
                clean_up(out_file)
        
        except Exception as e:
            print(f"Error processing date {date_str}: {str(e)}")
            error_log.append(date_str)
            save_error_log(error_log)
        
        # Delay to prevent IP blocking
        delay = random.uniform(3, 10)  # Random delay between 3 and 10 seconds
        print(f"Waiting for {delay:.2f} seconds before the next request...")
        time.sleep(delay)

        current_date -= timedelta(days=1)

# Example usage
if __name__ == "__main__":
    fetch_historical_data("30-08-2014", "30-08-2010")
