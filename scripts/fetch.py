import requests
import zipfile
import os
from io import BytesIO
import json
from collections import OrderedDict
from datetime import datetime, timedelta
import concurrent.futures
import urllib3

# Disable SSL warnings since we're disabling verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATE_FORMAT = '%m/%d/%Y'
DIRECT_IP = "144.126.254.118"

def download_and_extract_nav(date_str, url_variations):
    """
    Attempt to download and extract the NAV data for a given date using multiple URL variations.
    Returns the extracted file name if successful, otherwise returns None.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Host': 'npscra.nsdl.co.in'
    }

    for variation in url_variations:
        domain_url = variation.format(date_str=date_str)
        ip_url = domain_url.replace('npscra.nsdl.co.in', DIRECT_IP)
        print(f"Trying URL: {ip_url}")
        
        try:
            response = requests.get(ip_url, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                print(f"Successfully downloaded from: {ip_url}")
                try:
                    with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                        for file_name in zip_ref.namelist():
                            if file_name.endswith('.out'):
                                zip_ref.extract(file_name, os.getcwd())
                                print(f"Extracted: {file_name}")
                                return file_name
                except zipfile.BadZipFile:
                    print(f"Invalid ZIP file received from {ip_url}")
            
            elif response.status_code == 404:
                print(f"NAV file not available at {ip_url}")
            else:
                print(f"Failed to download from {ip_url}. Status code: {response.status_code}")
        
        except requests.RequestException as e:
            print(f"Error downloading from {ip_url}: {e}")
    
    return None

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
    os.makedirs(os.path.dirname(root_file), exist_ok=True)
    
    existing_data = []
    if os.path.exists(root_file):
        with open(root_file, 'r') as json_file:
            existing_data = json.load(json_file)
    
    all_data = existing_data + new_data
    latest_records = {}
    
    for record in all_data:
        key = (record["PFM Code"], record["Scheme Code"])
        if key not in latest_records or datetime.strptime(record["Date"], DATE_FORMAT) > datetime.strptime(latest_records[key]["Date"], DATE_FORMAT):
            latest_records[key] = record
    
    latest_data = list(latest_records.values())
    
    with open(root_file, 'w') as json_file:
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

        scheme_data[scheme["Date"]] = scheme["NAV"]
        sorted_scheme_data = OrderedDict(
            sorted(scheme_data.items(), key=lambda x: datetime.strptime(x[0], DATE_FORMAT), reverse=True)
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
                last_date = max(datetime.strptime(entry['Date'], DATE_FORMAT) for entry in data)
                return last_date
    return None

def process_date(date, url_variations):
    """Process a single date: download, extract, parse, and update data."""
    date_str = date.strftime("%d%m%Y")
    print(f"Trying to fetch NAV data for {date.strftime('%d-%m-%Y')}...")
    
    out_file = download_and_extract_nav(date_str, url_variations)
    
    if out_file:
        nav_data = parse_out_file(out_file)
        update_scheme_json(nav_data)
        clean_up(out_file)
        return nav_data
    else:
        print(f"No NAV data available for {date.strftime('%d-%m-%Y')}.")
        return []

if __name__ == "__main__":
    url_variations = [
        "https://npscra.nsdl.co.in/download/NAV_File_{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV_FILE_{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV_file_{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV%20File%20{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV%20FILE%20{date_str}.zip",
        "https://npscra.nsdl.co.in/download/nav%20file%20{date_str}.zip"
    ]
    
    last_date = get_last_date_in_data()
    today = datetime.now()
    
    if not last_date:
        last_date = datetime.strptime("30/08/2024", "%d/%m/%Y")

    all_nav_data = []

    current_date = last_date + timedelta(days=1)
    dates_to_process = [current_date + timedelta(days=i) for i in range((today - current_date).days + 1)]

    # Use ThreadPoolExecutor for concurrent processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_date = {executor.submit(process_date, date, url_variations): date for date in dates_to_process}
        for future in concurrent.futures.as_completed(future_to_date):
            date = future_to_date[future]
            try:
                nav_data = future.result()
                all_nav_data.extend(nav_data)
            except Exception as exc:
                print(f"Date {date} generated an exception: {exc}")

    if all_nav_data:
        save_latest_data(all_nav_data)
        print(f"Script completed. Total new records saved: {len(all_nav_data)}")
    else:
        print("No new data available. Existing data.json remains unchanged.")