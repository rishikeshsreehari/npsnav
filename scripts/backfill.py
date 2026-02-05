import requests
import pandas as pd
import os
import json
from collections import OrderedDict
from datetime import datetime, timedelta
import concurrent.futures
import urllib3
from io import BytesIO, StringIO
import tempfile
import time
import logging
import random

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATE_FORMAT = '%m/%d/%Y'
BASE_URL = "https://npstrust.org.in/scheme-wise-nav-report-excel"

# --- CONFIGURATION ---
# '60' retrieves the last 5 years (60 months) of data in one shot.
BACKFILL_MONTHS = '2' 

def get_pfm_scheme_mappings():
    """Extract PFM and Scheme mappings from existing data.json"""
    mappings = {}
    pfm_names = {}
    scheme_names = {}
    
    data_file = "data/data.json"
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            for record in data:
                pfm_code = record["PFM Code"]
                scheme_code = record["Scheme Code"]
                pfm_name = record["PFM Name"]
                scheme_name = record["Scheme Name"]
                
                if pfm_code not in mappings:
                    mappings[pfm_code] = set()
                mappings[pfm_code].add(scheme_code)
                
                pfm_names[pfm_code] = pfm_name
                scheme_names[scheme_code] = scheme_name
            
            for pfm_code in mappings:
                mappings[pfm_code] = list(mappings[pfm_code])
            
            logger.info(f"Loaded mappings for {len(mappings)} PFMs with {sum(len(schemes) for schemes in mappings.values())} total schemes")
            return mappings, pfm_names, scheme_names
            
        except Exception as e:
            logger.error(f"Error reading data.json: {e}")
    
    return {}, {}, {}

def get_existing_dates(scheme_code):
    """Get a set of all dates already present for a specific scheme"""
    scheme_file = os.path.join('data', f"{scheme_code}.json")
    existing_dates = set()
    
    if os.path.exists(scheme_file):
        try:
            with open(scheme_file, 'r') as f:
                scheme_data = json.load(f)
            if scheme_data:
                for date_str in scheme_data.keys():
                    try:
                        dt = datetime.strptime(date_str, DATE_FORMAT)
                        existing_dates.add(dt)
                    except ValueError:
                        continue
        except Exception as e:
            logger.warning(f"Could not read existing dates for {scheme_code}: {e}")
            
    return existing_dates

def try_read_file_alternative(file_content):
    """Try to read file with different approaches"""
    # Method 1: TSV
    try:
        text_content = file_content.decode('utf-8', errors='ignore')
        if text_content.startswith('ID\t') or 'DATE' in text_content[:100]:
            return pd.read_csv(StringIO(text_content), sep='\t')
    except Exception: pass
    
    # Method 2: CSV
    try:
        text_content = file_content.decode('utf-8', errors='ignore')
        return pd.read_csv(StringIO(text_content))
    except Exception: pass
    
    # Method 3: xlrd
    try:
        import xlrd
        with tempfile.NamedTemporaryFile(delete=True, suffix='.xls') as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()
            workbook = xlrd.open_workbook(tmp_file.name)
            sheet = workbook.sheet_by_index(0)
            data = []
            for row_idx in range(sheet.nrows):
                row_data = []
                for col_idx in range(sheet.ncols):
                    cell_value = sheet.cell_value(row_idx, col_idx)
                    if sheet.cell_type(row_idx, col_idx) == xlrd.XL_CELL_DATE:
                        date_tuple = xlrd.xldate_as_tuple(cell_value, workbook.datemode)
                        cell_value = datetime(*date_tuple)
                    row_data.append(cell_value)
                data.append(row_data)
            if data:
                return pd.DataFrame(data[1:], columns=data[0] if data else None)
    except Exception: pass
    
    # Method 4: openpyxl
    try:
        return pd.read_excel(BytesIO(file_content), engine='openpyxl')
    except Exception: pass
    
    # Method 5: calamine
    try:
        return pd.read_excel(BytesIO(file_content), engine='calamine')
    except Exception: pass
    
    raise Exception("All file reading methods failed")

def parse_date_string(date_str):
    if not date_str or pd.isna(date_str): return None, None
    date_str = str(date_str).strip()
    if date_str.lower() in ['date', 'date of nav', 'nan']: return None, None
    
    date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
    for fmt in date_formats:
        try:
            current_date = datetime.strptime(date_str, fmt)
            formatted_date = current_date.strftime(DATE_FORMAT)
            return current_date, formatted_date
        except ValueError: continue
    return None, None

def parse_excel_data(df, pfm_code, scheme_code, pfm_names, scheme_names):
    data_list = []
    try:
        if df.empty: return []
        
        # KEY LOGIC: Get existing dates so we only add what is missing
        existing_dates = get_existing_dates(scheme_code)
        
        pfm_name = pfm_names.get(pfm_code, "Unknown PFM")
        scheme_name = scheme_names.get(scheme_code, "Unknown Scheme")
        
        # Column finding logic
        date_col = None
        nav_col = None
        for i, col in enumerate(df.columns):
            col_str = str(col).lower().strip()
            if 'date' in col_str and 'nav' in col_str: date_col = i
            elif col_str == 'date of nav': date_col = i
            elif 'nav' in col_str and ('value' in col_str or col_str == 'nav value'): nav_col = i
        
        if date_col is None: date_col = 1 if len(df.columns) > 1 else 0
        if nav_col is None: nav_col = 6 if len(df.columns) > 6 else len(df.columns) - 1
        
        for index, row in df.iterrows():
            try:
                if len(row) <= max(date_col, nav_col): continue
                date_val = row.iloc[date_col] if date_col < len(row) else None
                nav_val = row.iloc[nav_col] if nav_col < len(row) else None
                
                if pd.isna(date_val) or pd.isna(nav_val): continue
                
                if isinstance(date_val, datetime):
                    current_date = date_val
                    formatted_date = date_val.strftime(DATE_FORMAT)
                else:
                    current_date, formatted_date = parse_date_string(str(date_val))
                
                if not formatted_date or not current_date: continue
                
                # CRITICAL: Skip if we already have this specific date
                if current_date in existing_dates:
                    continue
                
                try:
                    nav_value = str(float(nav_val))
                except: continue
                
                scheme_data = {
                    "Date": formatted_date,
                    "PFM Code": pfm_code,
                    "PFM Name": pfm_name,
                    "Scheme Code": scheme_code,
                    "Scheme Name": scheme_name,
                    "NAV": nav_value
                }
                data_list.append(scheme_data)
                existing_dates.add(current_date)
                
            except Exception: continue
        
        return data_list
    except Exception as e:
        logger.error(f"Error parsing data for {pfm_code}/{scheme_code}: {e}")
        return []

def download_nav_excel_single_shot(pfm_code, scheme_code, pfm_names, scheme_names, retry_count=3):
    """Download 5 years of data with Stealth features (Random Headers + Delays)"""
    
    # List of different browser identities
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    ]

    # Stealth Feature 1: Random wait before starting
    # This prevents all 4 workers from hitting the server simultaneously
    time.sleep(random.uniform(1.5, 4.5))

    headers = {
        # Stealth Feature 2: Pick a random browser identity for each request
        'User-Agent': random.choice(user_agents),
        'Accept': 'application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/plain,*/*',
        'Referer': 'https://npstrust.org.in/',
        'Connection': 'keep-alive'
    }
    
    params = {
        'navcatdataxls': pfm_code,
        'navyearselxls': BACKFILL_MONTHS, 
        'navsubdataxls': scheme_code
    }
    
    for attempt in range(retry_count):
        try:
            # logger.info(f"Downloading data for {pfm_code}/{scheme_code}...")
            response = requests.get(BASE_URL, params=params, headers=headers, verify=False, timeout=45)
            
            if response.status_code == 200 and len(response.content) > 0:
                try:
                    df = try_read_file_alternative(response.content)
                    data = parse_excel_data(df, pfm_code, scheme_code, pfm_names, scheme_names)
                    if data:
                        logger.info(f"Found {len(data)} NEW records for {scheme_code}")
                    else:
                        logger.info(f"No new records for {scheme_code}")
                    return data
                except Exception as e:
                    logger.error(f"Error parsing {scheme_code}: {e}")
                    if attempt == retry_count - 1: return []
            else:
                logger.warning(f"Failed {scheme_code} (Status: {response.status_code})")
                
        except requests.RequestException as e:
            logger.error(f"Network error {scheme_code}: {e}")
        
        # Exponential backoff for retries
        if attempt < retry_count - 1:
            time.sleep(2 ** attempt)
            
    return []

def update_scheme_json(new_data):
    if not os.path.exists('data'): os.makedirs('data')
    schemes_updated = {}
    for record in new_data:
        scheme_code = record["Scheme Code"]
        if scheme_code not in schemes_updated: schemes_updated[scheme_code] = []
        schemes_updated[scheme_code].append(record)
    
    for scheme_code, records in schemes_updated.items():
        scheme_file = os.path.join('data', f"{scheme_code}.json")
        try:
            if os.path.exists(scheme_file):
                with open(scheme_file, 'r') as f:
                    scheme_data = json.load(f, object_pairs_hook=OrderedDict)
            else:
                scheme_data = OrderedDict()
            
            for record in records:
                scheme_data[record["Date"]] = record["NAV"]
            
            sorted_scheme_data = OrderedDict(
                sorted(scheme_data.items(), key=lambda x: datetime.strptime(x[0], DATE_FORMAT), reverse=True)
            )
            
            with open(scheme_file, 'w') as f:
                json.dump(sorted_scheme_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error updating {scheme_file}: {e}")

def save_latest_data(new_data):
    root_file = "data/data.json"
    os.makedirs(os.path.dirname(root_file), exist_ok=True)
    try:
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
        
        with open(root_file, 'w') as json_file:
            json.dump(list(latest_records.values()), json_file, indent=4)
        logger.info(f"Main data.json updated.")
    except Exception as e:
        logger.error(f"Error saving latest data: {e}")

if __name__ == "__main__":
    logger.info("Starting DEEP BACKFILL ...")
    
    pfm_scheme_mappings, pfm_names, scheme_names = get_pfm_scheme_mappings()
    if not pfm_scheme_mappings:
        logger.error("No mappings found. Exiting.")
        exit(1)
    
    all_nav_data = []
    scheme_tasks = []
    for pfm_code, scheme_codes in pfm_scheme_mappings.items():
        for scheme_code in scheme_codes:
            scheme_tasks.append((pfm_code, scheme_code))
    
    logger.info(f"Processing {len(scheme_tasks)} schemes...")
    
    # max_workers=4 is safe with the added sleep delays
    max_workers = 4
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_scheme = {
            executor.submit(download_nav_excel_single_shot, pfm, scheme, pfm_names, scheme_names): (pfm, scheme) 
            for pfm, scheme in scheme_tasks
        }
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_scheme):
            pfm, scheme = future_to_scheme[future]
            completed += 1
            if completed % 5 == 0:
                logger.info(f"Progress: {completed}/{len(scheme_tasks)} schemes processed")
            
            try:
                data = future.result()
                if data: all_nav_data.extend(data)
            except Exception as exc:
                logger.error(f"Scheme {scheme} failed: {exc}")

    if all_nav_data:
        logger.info(f"Saving {len(all_nav_data)} total new records...")
        update_scheme_json(all_nav_data)
        save_latest_data(all_nav_data)
        logger.info("Backfill complete!")
    else:
        logger.info("No new data found.")