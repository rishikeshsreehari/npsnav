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

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATE_FORMAT = '%m/%d/%Y'
DISPLAY_DATE_FORMAT = '%d-%m-%Y'
BASE_URL = "https://npstrust.org.in/scheme-wise-nav-report-excel"

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
            
            # Convert sets to lists
            for pfm_code in mappings:
                mappings[pfm_code] = list(mappings[pfm_code])
            
            logger.info(f"Loaded mappings for {len(mappings)} PFMs with {sum(len(schemes) for schemes in mappings.values())} total schemes")
            return mappings, pfm_names, scheme_names
            
        except Exception as e:
            logger.error(f"Error reading data.json: {e}")
    
    return {}, {}, {}

def get_last_date_for_scheme(scheme_code):
    """Get the last date available for a specific scheme"""
    scheme_file = os.path.join('data', f"{scheme_code}.json")
    if os.path.exists(scheme_file):
        try:
            with open(scheme_file, 'r') as f:
                scheme_data = json.load(f)
            if scheme_data:
                # Get the most recent date (files are sorted in reverse chronological order)
                latest_date_str = list(scheme_data.keys())[0]
                return datetime.strptime(latest_date_str, DATE_FORMAT)
        except Exception as e:
            logger.warning(f"Could not get last date for {scheme_code}: {e}")
    return None

def try_read_file_alternative(file_content):
    """Try to read file with different approaches - TSV, CSV, or Excel"""
    
    # Method 1: Try as TSV (tab-separated) file first
    try:
        logger.debug("Trying to read as TSV (tab-separated) file...")
        # Decode content to text
        text_content = file_content.decode('utf-8', errors='ignore')
        
        # Check if it starts with expected headers
        if text_content.startswith('ID\t') or 'DATE' in text_content[:100]:
            # Read as TSV
            df = pd.read_csv(StringIO(text_content), sep='\t')
            logger.debug("Successfully read as TSV file")
            return df
    except Exception as e:
        logger.debug(f"TSV approach failed: {str(e)[:100]}...")
    
    # Method 2: Try as CSV file
    try:
        logger.debug("Trying to read as CSV file...")
        text_content = file_content.decode('utf-8', errors='ignore')
        df = pd.read_csv(StringIO(text_content))
        logger.debug("Successfully read as CSV file")
        return df
    except Exception as e:
        logger.debug(f"CSV approach failed: {str(e)[:100]}...")
    
    # Method 3: Try with xlrd directly
    try:
        logger.debug("Trying direct xlrd approach...")
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
                df = pd.DataFrame(data[1:], columns=data[0] if data else None)
                logger.debug("Successfully read Excel with direct xlrd approach")
                return df
                    
    except Exception as e:
        logger.debug(f"Direct xlrd approach failed: {str(e)[:100]}...")
    
    # Method 4: Try openpyxl
    try:
        logger.debug("Trying openpyxl...")
        df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
        logger.debug("Successfully read Excel with openpyxl")
        return df
    except Exception as e:
        logger.debug(f"openpyxl approach failed: {str(e)[:100]}...")
    
    # Method 5: Try calamine
    try:
        logger.debug("Trying calamine engine...")
        df = pd.read_excel(BytesIO(file_content), engine='calamine')
        logger.debug("Successfully read Excel with calamine")
        return df
    except Exception as e:
        logger.debug(f"calamine approach failed: {str(e)[:100]}...")
    
    raise Exception("All file reading methods failed")

def parse_date_string(date_str):
    """Parse date string with multiple format attempts"""
    if not date_str or pd.isna(date_str):
        return None, None
    
    date_str = str(date_str).strip()
    
    # Skip header rows
    if date_str.lower() in ['date', 'date of nav', 'nan']:
        return None, None
    
    # Try different date formats
    date_formats = [
        '%Y-%m-%d',      # 2025-07-04 (ISO format from TSV)
        '%d-%m-%Y',      # 04-07-2025
        '%d/%m/%Y',      # 04/07/2025
        '%m/%d/%Y',      # 07/04/2025
        '%Y/%m/%d',      # 2025/07/04
    ]
    
    for fmt in date_formats:
        try:
            current_date = datetime.strptime(date_str, fmt)
            formatted_date = current_date.strftime(DATE_FORMAT)
            return current_date, formatted_date
        except ValueError:
            continue
    
    return None, None

def download_nav_excel(pfm_code, scheme_code, pfm_names, scheme_names, retry_count=3):
    """Download NAV data for a specific PFM and scheme from npstrust.org.in"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/plain,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://npstrust.org.in/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    params = {
        'navcatdataxls': pfm_code,
        'navyearselxls': '12',  # Latest data
        'navsubdataxls': scheme_code
    }
    
    for attempt in range(retry_count):
        try:
            logger.info(f"Downloading NAV data for {pfm_code}/{scheme_code} (attempt {attempt + 1})")
            response = requests.get(BASE_URL, params=params, headers=headers, verify=False, timeout=30)
            
            if response.status_code == 200 and len(response.content) > 0:
                content_type = response.headers.get('content-type', '').lower()
                logger.debug(f"Response content type: {content_type}, size: {len(response.content)} bytes")
                
                try:
                    df = try_read_file_alternative(response.content)
                    return parse_excel_data(df, pfm_code, scheme_code, pfm_names, scheme_names)
                except Exception as e:
                    logger.error(f"Error parsing file for {pfm_code}/{scheme_code}: {e}")
                    if attempt == retry_count - 1:
                        return []
            else:
                logger.warning(f"Failed to download data for {pfm_code}/{scheme_code}. Status: {response.status_code}")
                if attempt == retry_count - 1:
                    return []
                    
        except requests.RequestException as e:
            logger.error(f"Error downloading {pfm_code}/{scheme_code} (attempt {attempt + 1}): {e}")
            if attempt == retry_count - 1:
                return []
        
        # Wait before retry
        if attempt < retry_count - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return []

def parse_excel_data(df, pfm_code, scheme_code, pfm_names, scheme_names):
    """Parse the data and extract NAV information"""
    data_list = []
    
    try:
        if df.empty:
            logger.warning(f"File is empty for {pfm_code}/{scheme_code}")
            return []
        
        # Get existing data to avoid duplicates
        last_date = get_last_date_for_scheme(scheme_code)
        
        pfm_name = pfm_names.get(pfm_code, "Unknown PFM")
        scheme_name = scheme_names.get(scheme_code, "Unknown Scheme")
        
        logger.debug(f"Data shape for {pfm_code}/{scheme_code}: {df.shape}")
        
        # Find date and NAV columns
        date_col = None
        nav_col = None
        pfm_name_col = None
        scheme_name_col = None
        
        for i, col in enumerate(df.columns):
            col_str = str(col).lower().strip()
            if 'date' in col_str and 'nav' in col_str:
                date_col = i
            elif col_str == 'date of nav':
                date_col = i
            elif 'nav' in col_str and ('value' in col_str or col_str == 'nav value'):
                nav_col = i
            elif 'pfm' in col_str and 'name' in col_str:
                pfm_name_col = i
            elif 'scheme' in col_str and 'name' in col_str:
                scheme_name_col = i
        
        # Fallback to positional
        if date_col is None:
            date_col = 1 if len(df.columns) > 1 else 0
        if nav_col is None:
            nav_col = 6 if len(df.columns) > 6 else len(df.columns) - 1
        if pfm_name_col is None and len(df.columns) > 3:
            pfm_name_col = 3
        if scheme_name_col is None and len(df.columns) > 5:
            scheme_name_col = 5
        
        # Try to get names from the data if available
        if not df.empty:
            try:
                if pfm_name_col is not None and not pd.isna(df.iloc[0, pfm_name_col]):
                    pfm_name = str(df.iloc[0, pfm_name_col])
                if scheme_name_col is not None and not pd.isna(df.iloc[0, scheme_name_col]):
                    scheme_name = str(df.iloc[0, scheme_name_col])
            except:
                pass
        
        new_records_count = 0
        
        # Process each row
        for index, row in df.iterrows():
            try:
                if len(row) <= max(date_col, nav_col):
                    continue
                
                date_val = row.iloc[date_col] if date_col < len(row) else None
                nav_val = row.iloc[nav_col] if nav_col < len(row) else None
                
                if pd.isna(date_val) or pd.isna(nav_val):
                    continue
                
                # Parse date
                if isinstance(date_val, datetime):
                    current_date = date_val
                    formatted_date = date_val.strftime(DATE_FORMAT)
                else:
                    current_date, formatted_date = parse_date_string(str(date_val))
                
                if not formatted_date or not current_date:
                    continue
                
                # Skip if we already have this date or newer
                if last_date and current_date <= last_date:
                    continue
                
                # Parse NAV value
                try:
                    nav_value = str(float(nav_val))
                except:
                    logger.debug(f"Could not parse NAV: {nav_val}")
                    continue
                
                scheme_data = {
                    "Date": formatted_date,
                    "PFM Code": pfm_code,
                    "PFM Name": pfm_name,
                    "Scheme Code": scheme_code,
                    "Scheme Name": scheme_name,
                    "NAV": nav_value
                }
                data_list.append(scheme_data)
                new_records_count += 1
                
            except Exception as e:
                logger.debug(f"Error processing row {index} for {pfm_code}/{scheme_code}: {e}")
                continue
        
        logger.info(f"Extracted {new_records_count} NEW records for {pfm_code}/{scheme_code}")
        return data_list
        
    except Exception as e:
        logger.error(f"Error parsing data for {pfm_code}/{scheme_code}: {e}")
        return []

def update_scheme_json(new_data):
    """Update individual JSON files for schemes with only NEW data"""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    schemes_updated = {}
    
    # Group new data by scheme
    for record in new_data:
        scheme_code = record["Scheme Code"]
        if scheme_code not in schemes_updated:
            schemes_updated[scheme_code] = []
        schemes_updated[scheme_code].append(record)
    
    # Update each scheme file
    for scheme_code, records in schemes_updated.items():
        scheme_file = os.path.join('data', f"{scheme_code}.json")
        
        try:
            # Load existing data
            if os.path.exists(scheme_file):
                with open(scheme_file, 'r') as f:
                    scheme_data = json.load(f, object_pairs_hook=OrderedDict)
            else:
                scheme_data = OrderedDict()
            
            # Add new records
            for record in records:
                scheme_data[record["Date"]] = record["NAV"]
            
            # Sort by date (newest first)
            sorted_scheme_data = OrderedDict(
                sorted(scheme_data.items(), key=lambda x: datetime.strptime(x[0], DATE_FORMAT), reverse=True)
            )
            
            # Save updated file
            with open(scheme_file, 'w') as f:
                json.dump(sorted_scheme_data, f, indent=4)
            
            logger.info(f"Updated {scheme_file} with {len(records)} new records")
        except Exception as e:
            logger.error(f"Error updating {scheme_file}: {e}")

def save_latest_data(new_data):
    """Save the latest NAV data to data.json"""
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
        
        latest_data = list(latest_records.values())
        
        with open(root_file, 'w') as json_file:
            json.dump(latest_data, json_file, indent=4)
        
        logger.info(f"Latest data saved to {root_file} with {len(new_data)} new records")
    except Exception as e:
        logger.error(f"Error saving latest data: {e}")

def process_scheme(pfm_code, scheme_code, pfm_names, scheme_names):
    """Process a single scheme: download, extract, parse, and return new data only"""
    try:
        nav_data = download_nav_excel(pfm_code, scheme_code, pfm_names, scheme_names)
        
        if nav_data:
            logger.info(f"Found {len(nav_data)} new records for {pfm_code}/{scheme_code}")
            return nav_data
        else:
            logger.debug(f"No new NAV data for {pfm_code}/{scheme_code}")
            return []
    except Exception as e:
        logger.error(f"Error processing scheme {pfm_code}/{scheme_code}: {e}")
        return []

if __name__ == "__main__":
    logger.info("Starting NAV data fetch process...")
    
    # Get mappings from existing data.json
    pfm_scheme_mappings, pfm_names, scheme_names = get_pfm_scheme_mappings()
    
    if not pfm_scheme_mappings:
        logger.error("No scheme mappings found. Cannot proceed.")
        exit(1)
    
    all_nav_data = []
    
    # Process all PFM-scheme combinations
    scheme_tasks = []
    for pfm_code, scheme_codes in pfm_scheme_mappings.items():
        for scheme_code in scheme_codes:
            scheme_tasks.append((pfm_code, scheme_code))
    
    logger.info(f"Processing {len(scheme_tasks)} scheme combinations...")
    
    # Use ThreadPoolExecutor for concurrent processing
    max_workers = 3  # Conservative for production
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_scheme = {
            executor.submit(process_scheme, pfm_code, scheme_code, pfm_names, scheme_names): (pfm_code, scheme_code) 
            for pfm_code, scheme_code in scheme_tasks
        }
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_scheme):
            pfm_code, scheme_code = future_to_scheme[future]
            completed += 1
            try:
                nav_data = future.result()
                all_nav_data.extend(nav_data)
                if completed % 10 == 0:  # Progress indicator
                    logger.info(f"Completed {completed}/{len(scheme_tasks)} schemes")
            except Exception as exc:
                logger.error(f"Scheme {pfm_code}/{scheme_code} generated an exception: {exc}")

    if all_nav_data:
        # Update individual scheme files with new data only
        update_scheme_json(all_nav_data)
        # Update main data.json
        save_latest_data(all_nav_data)
        logger.info(f"Script completed successfully. Total new records saved: {len(all_nav_data)}")
    else:
        logger.info("No new data available. Files remain unchanged.")