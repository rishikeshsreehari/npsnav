import requests
import zipfile
import os
from io import BytesIO
import json
from collections import OrderedDict
from datetime import datetime, timedelta
import urllib3
import sys
import shutil

# Disable SSL warnings since we're disabling verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATE_FORMAT = '%m/%d/%Y'
DIRECT_IP = "144.126.254.118"

# =============================================================================
# CONFIGURATION - MODIFY THESE AS NEEDED
# =============================================================================

# MODE SELECTION: Choose between 'range' or 'specific'
MODE = "specific"  # Options: "range" or "specific"

# FOR RANGE MODE - will scan for missing dates between these dates
RANGE_START_DATE = "01/01/2015"  # DD/MM/YYYY format - earliest date to check
RANGE_END_DATE = "05/06/2025"    # DD/MM/YYYY format - latest date to check (will go backwards from here)

# FOR SPECIFIC DATES MODE - list specific dates to update
SPECIFIC_DATES = [
"10/02/2020", "04/02/2020", "03/02/2020", "22/07/2019", "07/08/2015"
]

# =============================================================================

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create debug_files directory if it doesn't exist
if not os.path.exists('debug_files'):
    os.makedirs('debug_files')

# Create log file with timestamp
log_filename = f"logs/nav_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

class Logger:
    def __init__(self, log_file):
        self.log_file = log_file
        # Write initial header
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"NAV Data Update Log\n")
            f.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
    
    def log(self, message, also_print=True):
        """Log message to file and optionally print to console"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        # Write to file immediately (flush to ensure it's written even if program crashes)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                f.flush()  # Force write to disk
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        # Also print to console if requested
        if also_print:
            print(f"[{timestamp}] {message}")
    
    def log_error(self, message, exception=None):
        """Log error messages"""
        error_msg = f"ERROR: {message}"
        if exception:
            error_msg += f" - {str(exception)}"
        self.log(error_msg)
    
    def log_success(self, message):
        """Log success messages"""
        self.log(f"SUCCESS: {message}")
    
    def log_section(self, title):
        """Log section headers"""
        separator = "="*60
        self.log(f"\n{separator}")
        self.log(f"{title}")
        self.log(f"{separator}")

# Initialize logger
logger = Logger(log_filename)

def is_market_day(date):
    """
    Check if a date is a market day (exclude weekends).
    Monday=0, Tuesday=1, ..., Saturday=5, Sunday=6
    """
    return date.weekday() < 5  # Monday to Friday (0-4)

def parse_date_config(date_str):
    """Parse date string in DD/MM/YYYY format to datetime object"""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError as e:
        logger.log_error(f"Invalid date format: {date_str}. Expected DD/MM/YYYY format", e)
        raise

def convert_date_format(date_str):
    """
    Convert date from various formats to MM/DD/YYYY format (our standard)
    Handles: YYYYMMDD, DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY, YYYY-MM-DD
    """
    try:
        # Strip quotes first if present
        date_str = date_str.strip('"').strip()
        
        # First try YYYYMMDD format (most common)
        if len(date_str) == 8 and date_str.isdigit():
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            return date_obj.strftime(DATE_FORMAT)
        
        # Try formats with slashes
        elif '/' in date_str:
            # First try DD/MM/YYYY
            try:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                return date_obj.strftime(DATE_FORMAT)  # Convert to MM/DD/YYYY
            except ValueError:
                # If that fails, try MM/DD/YYYY (already in correct format)
                try:
                    datetime.strptime(date_str, DATE_FORMAT)  # Validate format
                    return date_str  # Already in MM/DD/YYYY format
                except ValueError:
                    raise ValueError(f"Unknown date format with slashes: {date_str}")
        
        # Try formats with dashes
        elif '-' in date_str:
            try:
                # Try DD-MM-YYYY
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                return date_obj.strftime(DATE_FORMAT)
            except ValueError:
                try:
                    # Try YYYY-MM-DD
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    return date_obj.strftime(DATE_FORMAT)
                except ValueError:
                    raise ValueError(f"Unknown date format with dashes: {date_str}")
        
        else:
            raise ValueError(f"Unknown date format: {date_str}")
            
    except ValueError as e:
        # Don't log error here to avoid spam, let the calling function handle it
        return None

def save_problematic_file(file_name, date_str):
    """Save a copy of problematic files for manual inspection"""
    debug_file = os.path.join('debug_files', f"debug_{date_str}_{file_name}")
    try:
        shutil.copy2(file_name, debug_file)
        logger.log(f"Saved problematic file to: {debug_file}")
    except Exception as e:
        logger.log_error(f"Failed to save debug file", e)

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

    for i, variation in enumerate(url_variations, 1):
        domain_url = variation.format(date_str=date_str)
        domain_headers = headers.copy()
        domain_headers['Host'] = 'npscra.nsdl.co.in'
        
        logger.log(f"  Trying URL variation {i}/{len(url_variations)}: {domain_url}")
        
        try:
            response = requests.get(domain_url, headers=domain_headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                logger.log(f"Downloaded ZIP file from: {domain_url}")
                try:
                    with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                        for file_name in zip_ref.namelist():
                            if file_name.endswith('.out'):
                                zip_ref.extract(file_name, os.getcwd())
                                logger.log(f"Extracted: {file_name}")
                                return file_name
                except zipfile.BadZipFile:
                    logger.log_error(f"Invalid ZIP file received from {domain_url}")
                    continue
            
            elif response.status_code == 404:
                logger.log(f"  Domain URL returned 404, trying IP fallback...")
                # Try IP fallback
                ip_url = domain_url.replace('npscra.nsdl.co.in', DIRECT_IP)
                ip_headers = headers.copy()
                ip_headers['Host'] = 'npscra.nsdl.co.in'
                
                logger.log(f"  IP fallback URL: {ip_url}")
                
                try:
                    response = requests.get(ip_url, headers=ip_headers, verify=False, timeout=30)
                    if response.status_code == 200:
                        logger.log(f"Downloaded ZIP file from IP fallback: {ip_url}")
                        try:
                            with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                                for file_name in zip_ref.namelist():
                                    if file_name.endswith('.out'):
                                        zip_ref.extract(file_name, os.getcwd())
                                        logger.log(f"Extracted: {file_name}")
                                        return file_name
                        except zipfile.BadZipFile:
                            logger.log_error(f"Invalid ZIP file received from IP {ip_url}")
                            continue
                    elif response.status_code == 404:
                        logger.log(f"  IP fallback also returned 404")
                    else:
                        logger.log(f"  IP fallback failed with status: {response.status_code}")
                except requests.RequestException as e:
                    logger.log_error(f"IP fallback request failed for {ip_url}", e)
            else:
                logger.log(f"  Domain URL failed with status: {response.status_code}")
        
        except requests.RequestException as e:
            logger.log_error(f"Request failed for {domain_url}", e)
            # Try IP fallback for connection errors too
            try:
                ip_url = domain_url.replace('npscra.nsdl.co.in', DIRECT_IP)
                ip_headers = headers.copy()
                ip_headers['Host'] = 'npscra.nsdl.co.in'
                
                logger.log(f"  Trying IP fallback due to connection error: {ip_url}")
                
                response = requests.get(ip_url, headers=ip_headers, verify=False, timeout=30)
                if response.status_code == 200:
                    logger.log(f"Downloaded ZIP file from IP fallback: {ip_url}")
                    try:
                        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                            for file_name in zip_ref.namelist():
                                if file_name.endswith('.out'):
                                    zip_ref.extract(file_name, os.getcwd())
                                    logger.log(f"Extracted: {file_name}")
                                    return file_name
                    except zipfile.BadZipFile:
                        logger.log_error(f"Invalid ZIP file from IP {ip_url}")
                        continue
            except requests.RequestException as e2:
                logger.log_error(f"IP fallback also failed for {ip_url}", e2)
    
    return None

def parse_out_file(file_name):
    """Parse the .out file and extract the NAV data with proper format detection."""
    logger.log(f"Parsing file: {file_name}")
    data_list = []
    invalid_dates = 0
    
    try:
        # First, examine the raw content to understand the format
        with open(file_name, 'rb') as file:
            raw_sample = file.read(200)
            logger.log(f"Raw file sample: {raw_sample}")
        
        # Determine the correct format based on file content
        if b'\t' in raw_sample:
            # Tab-delimited format (2017 onwards)
            logger.log("Detected TAB-delimited format")
            delimiter = '\t'
            expected_columns = 10
            
            # Determine column mapping based on first column content
            if raw_sample.startswith(b'0\t') or raw_sample.startswith(b'"0\t'):
                # Modern format: 0, Date, PFM_Code, PFM_Name, Scheme_Code, Scheme_Name, NAV, admin, Date2, Flag
                date_col, pfm_code_col, pfm_name_col, scheme_code_col, scheme_name_col, nav_col = 1, 2, 3, 4, 5, 6
                logger.log("Using modern TAB format (2020+)")
            elif raw_sample.startswith(b'DEFAULT\t'):
                # Older format: DEFAULT, Date, PFM_Code, PFM_Name, Scheme_Code, Scheme_Name, NAV, admin, Date2, Flag
                date_col, pfm_code_col, pfm_name_col, scheme_code_col, scheme_name_col, nav_col = 1, 2, 3, 4, 5, 6
                logger.log("Using older TAB format (2017-2019)")
            else:
                logger.log("Unknown TAB format, using default mapping")
                date_col, pfm_code_col, pfm_name_col, scheme_code_col, scheme_name_col, nav_col = 1, 2, 3, 4, 5, 6
                
        elif b',' in raw_sample:
            # Comma-delimited format (2015-2016)
            logger.log("Detected COMMA-delimited format")
            delimiter = ','
            expected_columns = 5
            
            # Check if it's the malformed 2015 format
            if b'"' in raw_sample and (b'PFM001,' in raw_sample or b'PFM001SBI' in raw_sample):
                logger.log("Detected malformed 2015 format - attempting to fix")
                # This needs special handling
                return parse_malformed_2015_format(file_name)
            else:
                # Normal comma format: Date, PFM_Code, PFM_Name, Scheme_Code, Scheme_Name, NAV
                date_col, pfm_code_col, pfm_name_col, scheme_code_col, scheme_name_col, nav_col = 0, 1, 2, 3, 4, 5
                
        else:
            logger.log_error("Unknown file format - no tabs or commas detected")
            return []

        # Parse the file with the detected format
        with open(file_name, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                    
                columns = line.split(delimiter)
                
                if line_num <= 5:  # Debug first 5 lines
                    logger.log(f"Line {line_num}: {len(columns)} columns with '{delimiter}' - {columns[:6] if len(columns) >= 6 else columns}")
                
                if len(columns) >= expected_columns:
                    try:
                        # Extract data based on format
                        raw_date = columns[date_col].strip('"').strip()
                        pfm_code = columns[pfm_code_col].strip('"').strip()
                        pfm_name = columns[pfm_name_col].strip('"').strip()
                        scheme_code = columns[scheme_code_col].strip('"').strip()
                        scheme_name = columns[scheme_name_col].strip('"').strip()
                        nav_value = columns[nav_col].strip('"').strip()
                        
                        # Convert date format
                        converted_date = convert_date_format(raw_date)
                        
                        if converted_date and scheme_code and nav_value:
                            # Validate NAV value
                            try:
                                float(nav_value)  # Test if it's a valid number
                                
                                scheme_data = {
                                    "Date": converted_date,
                                    "PFM Code": pfm_code,
                                    "PFM Name": pfm_name,
                                    "Scheme Code": scheme_code,
                                    "Scheme Name": scheme_name,
                                    "NAV": nav_value
                                }
                                data_list.append(scheme_data)
                                
                            except ValueError:
                                if line_num <= 10:
                                    logger.log(f"Line {line_num}: Invalid NAV value '{nav_value}'")
                        else:
                            invalid_dates += 1
                            if invalid_dates <= 5:
                                logger.log(f"Line {line_num}: Invalid data - date='{raw_date}', scheme='{scheme_code}', nav='{nav_value}'")
                            elif invalid_dates == 6:
                                logger.log("... (suppressing further invalid data warnings)")
                                
                    except IndexError as e:
                        if line_num <= 10:
                            logger.log(f"Line {line_num}: Index error - {e}")
                        continue
                        
                else:
                    if line_num <= 10:
                        logger.log(f"Line {line_num}: Insufficient columns - expected {expected_columns}, got {len(columns)}")

        logger.log(f"Parsed {len(data_list)} valid entries from {file_name}")
        if invalid_dates > 0:
            logger.log(f"Skipped {invalid_dates} invalid entries")
            
    except Exception as e:
        logger.log_error(f"Error parsing file {file_name}", e)
    
    return data_list

def parse_malformed_2015_format(file_name):
    """Special parser for malformed 2015 format files."""
    logger.log("Using special parser for malformed 2015 format")
    data_list = []
    
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip().strip('"')  # Remove outer quotes
                
                if not line:
                    continue
                
                # Try to fix the malformed format
                # Format: "MM/DD/YYYYPFM001,Company Name,Scheme Code,Scheme Name,NAV"
                # or: "MM/DD/YYYY,PFM001Company Name,Scheme Code,Scheme Name,NAV"
                
                if line_num <= 5:
                    logger.log(f"Raw line {line_num}: '{line}'")
                
                # Try different patterns to extract the data
                import re
                
                # Pattern 1: Date+PFM001,Company,Scheme,Name,NAV
                pattern1 = r'(\d{2}/\d{2}/\d{4})PFM001,([^,]+),([^,]+),([^,]+),([^,]+)$'
                match = re.match(pattern1, line)
                
                if not match:
                    # Pattern 2: Date,PFM001+Company,Scheme,Name,NAV
                    pattern2 = r'(\d{2}/\d{2}/\d{4}),PFM001([^,]+),([^,]+),([^,]+),([^,]+)$'
                    match = re.match(pattern2, line)
                
                if match:
                    date_str = match.group(1)
                    if len(match.groups()) == 5:
                        pfm_name = match.group(2).strip()
                        scheme_code = match.group(3).strip()
                        scheme_name = match.group(4).strip()
                        nav_value = match.group(5).strip()
                    else:
                        continue
                    
                    # Convert date format
                    converted_date = convert_date_format(date_str)
                    
                    if converted_date and scheme_code and nav_value:
                        try:
                            float(nav_value)  # Validate NAV
                            
                            scheme_data = {
                                "Date": converted_date,
                                "PFM Code": "PFM001",
                                "PFM Name": pfm_name,
                                "Scheme Code": scheme_code,
                                "Scheme Name": scheme_name,
                                "NAV": nav_value
                            }
                            data_list.append(scheme_data)
                            
                            if line_num <= 5:
                                logger.log(f"Parsed line {line_num}: {scheme_code} = {nav_value}")
                                
                        except ValueError:
                            if line_num <= 5:
                                logger.log(f"Invalid NAV on line {line_num}: '{nav_value}'")
                else:
                    if line_num <= 5:
                        logger.log(f"No match for line {line_num}: '{line[:100]}'")
        
        logger.log(f"Malformed 2015 parser: extracted {len(data_list)} valid entries")
        
    except Exception as e:
        logger.log_error(f"Error in malformed 2015 parser", e)
    
    return data_list


def find_missing_dates(start_date_str, end_date_str):
    """
    Find dates that are missing from our data by checking backwards from end_date to start_date.
    Excludes weekends and non-fund JSON files.
    """
    logger.log_section("SCANNING FOR MISSING DATES")
    
    # Parse the date strings - FIXED: Use the actual parameters, not global config
    try:
        start_date = parse_date_config(start_date_str)
        end_date = parse_date_config(end_date_str)
        
        # Log the actual dates being used
        logger.log(f"PARSED START DATE: {start_date.strftime('%d-%m-%Y')} from config '{start_date_str}'")
        logger.log(f"PARSED END DATE: {end_date.strftime('%d-%m-%Y')} from config '{end_date_str}'")
        
    except ValueError:
        return [], 0, 0
    
    if start_date > end_date:
        logger.log_error(f"Start date ({start_date_str}) cannot be after end date ({end_date_str})")
        return [], 0, 0
    
    # Files to exclude from fund file checking
    exclude_files = {'data.json', 'nifty.json', 'sensex.json', 'summary.json', 'index.json', 'banknifty.json'}
    
    logger.log(f"Scanning from {end_date.strftime('%d-%m-%Y')} back to {start_date.strftime('%d-%m-%Y')}")
    logger.log("Excluding weekends (Saturday and Sunday)")
    logger.log(f"Excluding non-fund files: {exclude_files}")
    
    missing_dates = []
    weekends_skipped = 0
    market_days_checked = 0
    current_date = end_date  # FIXED: This should use the parameter end_date
    
    logger.log(f"Starting scan from: {current_date.strftime('%d-%m-%Y')}")
    
    while current_date >= start_date:
        if is_market_day(current_date):
            market_days_checked += 1
            date_str = current_date.strftime(DATE_FORMAT)
            date_found = False
            
            # Check only fund files
            data_dir = "data"
            if os.path.exists(data_dir):
                fund_files = [f for f in os.listdir(data_dir) 
                             if f.endswith('.json') and f not in exclude_files]
                
                # Check first few fund files
                files_checked = 0
                files_with_date = 0
                check_limit = min(5, len(fund_files))  # Check first 5 fund files
                
                for filename in fund_files[:check_limit]:
                    fund_file = os.path.join(data_dir, filename)
                    try:
                        with open(fund_file, 'r') as f:
                            fund_data = json.load(f)
                            if date_str in fund_data:
                                files_with_date += 1
                            files_checked += 1
                    except (json.JSONDecodeError, FileNotFoundError):
                        continue
                
                # Date exists if found in majority of checked files
                if files_checked > 0:
                    date_found = (files_with_date / files_checked) >= 0.6  # 60% threshold
            
            if not date_found:
                missing_dates.append(current_date)
                logger.log(f"Missing: {current_date.strftime('%d-%m-%Y')} ({current_date.strftime('%A')}) - found in {files_with_date}/{files_checked} fund files")
            else:
                logger.log(f"Found: {current_date.strftime('%d-%m-%Y')} ({current_date.strftime('%A')}) - found in {files_with_date}/{files_checked} fund files")
        else:
            weekends_skipped += 1
            logger.log(f"Skipped: {current_date.strftime('%d-%m-%Y')} ({current_date.strftime('%A')}) - Weekend")
        
        current_date -= timedelta(days=1)
    
    # Sort missing dates (most recent first)
    missing_dates.sort(reverse=True)
    
    logger.log(f"\nScan complete:")
    logger.log(f"  - Date range: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}")
    logger.log(f"  - Total missing market days: {len(missing_dates)}")
    logger.log(f"  - Market days checked: {market_days_checked}")
    logger.log(f"  - Weekends skipped: {weekends_skipped}")
    logger.log(f"  - Total days scanned: {(end_date - start_date).days + 1}")
    
    return missing_dates, market_days_checked, weekends_skipped

def get_specific_dates():
    """
    Convert specific dates from config to datetime objects, filtering out weekends.
    """
    logger.log_section("PROCESSING SPECIFIC DATES")
    
    valid_dates = []
    invalid_dates = []
    weekends_skipped = []
    
    for date_str in SPECIFIC_DATES:
        try:
            date_obj = parse_date_config(date_str)
            if is_market_day(date_obj):
                valid_dates.append(date_obj)
                logger.log(f"Added: {date_obj.strftime('%d-%m-%Y')} ({date_obj.strftime('%A')})")
            else:
                weekends_skipped.append(date_str)
                logger.log(f"Skipped: {date_obj.strftime('%d-%m-%Y')} ({date_obj.strftime('%A')}) - Weekend")
        except ValueError:
            invalid_dates.append(date_str)
            logger.log_error(f"Invalid date format: {date_str}")
    
    # Sort dates (most recent first)
    valid_dates.sort(reverse=True)
    
    logger.log(f"\nSpecific dates processing complete:")
    logger.log(f"  - Valid market days to process: {len(valid_dates)}")
    logger.log(f"  - Weekends skipped: {len(weekends_skipped)}")
    logger.log(f"  - Invalid date formats: {len(invalid_dates)}")
    
    return valid_dates, len(weekends_skipped), len(invalid_dates)

def update_fund_json_files(nav_data):
    """Update individual fund JSON files with new NAV data."""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    updated_funds = []
    
    # Group data by scheme code
    schemes_data = {}
    for entry in nav_data:
        scheme_code = entry["Scheme Code"]
        if scheme_code not in schemes_data:
            schemes_data[scheme_code] = []
        schemes_data[scheme_code].append(entry)
    
    logger.log(f"Processing {len(schemes_data)} fund files...")
    
    # Update each fund's JSON file
    for scheme_code, entries in schemes_data.items():
        scheme_file = os.path.join('data', f"{scheme_code}.json")
        
        try:
            # Load existing data
            if os.path.exists(scheme_file):
                with open(scheme_file, 'r') as f:
                    scheme_data = json.load(f, object_pairs_hook=OrderedDict)
            else:
                scheme_data = OrderedDict()
                logger.log(f"  Creating new file: {scheme_code}.json")
            
            # Add new entries (there should typically be only one entry per scheme per date)
            new_entries_added = 0
            for entry in entries:
                date_key = entry["Date"]
                if date_key not in scheme_data:
                    scheme_data[date_key] = entry["NAV"]
                    new_entries_added += 1
                else:
                    logger.log(f"  Date {date_key} already exists in {scheme_code}.json, skipping")
            
            if new_entries_added > 0:
                # Sort by date (most recent first)
                sorted_scheme_data = OrderedDict(
                    sorted(scheme_data.items(), 
                          key=lambda x: datetime.strptime(x[0], DATE_FORMAT), 
                          reverse=True)
                )
                
                # Save updated data
                with open(scheme_file, 'w') as f:
                    json.dump(sorted_scheme_data, f, indent=4)
                
                updated_funds.append(scheme_code)
                logger.log(f"  Successfully updated {scheme_code}.json (+{new_entries_added} entries)")
            else:
                logger.log(f"  No new entries to add for {scheme_code}.json")
        
        except Exception as e:
            logger.log_error(f"Failed to update {scheme_code}.json", e)
    
    return updated_funds

def process_dates(dates_to_process, mode_name):
    """Process a list of dates and update NAV data."""
    if not dates_to_process:
        logger.log_success(f"No dates to process in {mode_name} mode!")
        return [], [], [], 0
    
    url_variations = [
        "https://npscra.nsdl.co.in/download/NAV_File_{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV_FILE_{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV_file_{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV%20File%20{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV%20FILE%20{date_str}.zip",
        "https://npscra.nsdl.co.in/download/nav%20file%20{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV_File{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV_FILE{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV_file{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV%20File{date_str}.zip",
        "https://npscra.nsdl.co.in/download/NAV%20FILE{date_str}.zip",
        "https://npscra.nsdl.co.in/download/nav%20file{date_str}.zip"
    ]
    
    dates_successfully_updated = []
    dates_no_data = []
    dates_found_but_failed_update = []
    total_updated_funds = 0
    
    logger.log_section(f"PROCESSING {len(dates_to_process)} DATES IN {mode_name.upper()} MODE")
    
    for i, date in enumerate(dates_to_process, 1):
        date_str = date.strftime("%d%m%Y")
        date_display = date.strftime('%d-%m-%Y (%A)')
        
        logger.log_section(f"PROCESSING DATE {i}/{len(dates_to_process)}: {date_display}")
        
        # Try to download data for this date
        out_file = download_and_extract_nav(date_str, url_variations)
        
        if out_file:
            logger.log(f"Data file downloaded and extracted for {date_display}")
            
            # Parse the .out file
            nav_data = parse_out_file(out_file)
            
            if nav_data:
                # Update fund JSON files
                updated_funds = update_fund_json_files(nav_data)
                
                if updated_funds:
                    total_updated_funds += len(updated_funds)
                    dates_successfully_updated.append(date_display)
                    logger.log_success(f"SUCCESSFULLY UPDATED {len(updated_funds)} fund files for {date_display} with {len(nav_data)} entries")
                else:
                    dates_found_but_failed_update.append(date_display)
                    logger.log_error(f"Data found for {date_display} but failed to update any fund files")
            else:
                # Save problematic file for manual inspection
                save_problematic_file(out_file, date_str)
                dates_found_but_failed_update.append(date_display)
                logger.log_error(f"Data downloaded for {date_display} but no valid entries found in parsed file")
            
            # Clean up the .out file
            if os.path.exists(out_file):
                os.remove(out_file)
                logger.log(f"Cleaned up: {out_file}")
        else:
            logger.log(f"No data available for {date_display}")
            dates_no_data.append(date_display)
    
    return dates_successfully_updated, dates_no_data, dates_found_but_failed_update, total_updated_funds

def main():
   """Main function to process dates based on selected mode."""
   try:
       logger.log_section("STARTING NAV DATA UPDATE PROCESS")
       logger.log_section("CONFIGURATION")
       logger.log(f"Mode: {MODE.upper()}")
       
       if MODE.lower() == "range":
           logger.log(f"Range Start Date: {RANGE_START_DATE} (earliest date to check)")
           logger.log(f"Range End Date: {RANGE_END_DATE} (latest date to check - going backwards from here)")
           
           # FIXED: Pass the actual config values to the function
           missing_dates, total_market_days, total_weekends = find_missing_dates(RANGE_START_DATE, RANGE_END_DATE)
           dates_to_process = missing_dates
           mode_name = "Range"
           
       elif MODE.lower() == "specific":
           logger.log(f"Specific Dates: {SPECIFIC_DATES}")
           
           # Get specific dates
           specific_dates, weekends_skipped, invalid_dates = get_specific_dates()
           dates_to_process = specific_dates
           mode_name = "Specific"
           total_market_days = len(specific_dates)
           total_weekends = weekends_skipped
           
       else:
           logger.log_error(f"Invalid MODE: {MODE}. Must be 'range' or 'specific'")
           return
       
       # Process the dates
       dates_successfully_updated, dates_no_data, dates_found_but_failed_update, total_updated_funds = process_dates(dates_to_process, mode_name)
       
       # Final summary with numbers first, then dates
       logger.log_section("FINAL SUMMARY")
       logger.log(f"Mode: {MODE.upper()}")
       
       if MODE.lower() == "range":
           start_date_obj = parse_date_config(RANGE_START_DATE)
           end_date_obj = parse_date_config(RANGE_END_DATE)
           total_days_in_range = (end_date_obj - start_date_obj).days + 1
           logger.log(f"Date range processed: {RANGE_START_DATE} to {RANGE_END_DATE}")
           logger.log(f"Total days in range: {total_days_in_range}")
           logger.log(f"Total market days (Mon-Fri) in range: {total_market_days}")
           logger.log(f"Total weekends skipped: {total_weekends}")
           logger.log(f"Missing market days found: {len(dates_to_process)}")
       else:
           logger.log(f"Specific dates requested: {len(SPECIFIC_DATES)}")
           logger.log(f"Valid market days to process: {len(dates_to_process)}")
           logger.log(f"Weekends skipped: {total_weekends}")
       
       # NUMBERS SUMMARY
       logger.log_section("SUMMARY BY NUMBERS")
       logger.log(f"✓ Days successfully updated: {len(dates_successfully_updated)}")
       logger.log(f"✗ Days with no data available: {len(dates_no_data)}")
       logger.log(f"⚠ Days with data but update failed: {len(dates_found_but_failed_update)}")
       logger.log(f"📁 Total fund files updated: {total_updated_funds}")
       
       # DETAILED DATES SUMMARY
       logger.log_section("DETAILED DATES BREAKDOWN")
       
       if dates_successfully_updated:
           logger.log(f"\n✓ DATES SUCCESSFULLY UPDATED ({len(dates_successfully_updated)}):")
           for date in dates_successfully_updated:
               logger.log(f"  ✓ {date}")
       
       if dates_no_data:
           logger.log(f"\n✗ DATES WITH NO DATA AVAILABLE ({len(dates_no_data)}):")
           for date in dates_no_data:
               logger.log(f"  ✗ {date}")
       
       if dates_found_but_failed_update:
           logger.log(f"\n⚠ DATES WITH DATA BUT UPDATE FAILED ({len(dates_found_but_failed_update)}):")
           for date in dates_found_but_failed_update:
               logger.log(f"  ⚠ {date}")
       
       # FINAL STATUS
       if dates_successfully_updated:
           logger.log_success(f"\nProcess completed! Successfully updated data for {len(dates_successfully_updated)} out of {len(dates_to_process)} dates.")
       else:
           logger.log(f"\nProcess completed but no dates were successfully updated.")
           
       # If there were any problematic files, let user know
       if dates_found_but_failed_update:
           logger.log(f"\nProblematic files have been saved to the 'debug_files' folder for manual inspection.")
       
   except Exception as e:
       logger.log_error("Critical error in main process", e)
       raise

if __name__ == "__main__":
   try:
       logger.log("Starting NAV data update process...")
       logger.log(f"Log file: {log_filename}")
       logger.log(f"Configuration: Mode = {MODE}")
       if MODE.lower() == "range":
           logger.log(f"Range: {RANGE_START_DATE} to {RANGE_END_DATE}")
       else:
           logger.log(f"Specific dates: {SPECIFIC_DATES}")
       main()
       logger.log("Process completed!")
   except Exception as e:
       logger.log_error("Critical error in main execution", e)
       print(f"\nCheck the log file for details: {log_filename}")
   finally:
       logger.log(f"\nProcess ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")