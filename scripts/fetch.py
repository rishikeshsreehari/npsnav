import requests
import pandas as pd
import os
import sys
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
DISCOVERY_URL = "https://npstrust.org.in/nav-report-excel"
PROTEAN_URL = "https://www.npscra.proteantech.in/download/NAV_File_{date_str}.zip"
# NPS Trust started silently remapping old POP codes to DIRECT on the per-scheme endpoint
# around this date. Entries on/after this date in old POP JSON files are corrupted.
CORRUPTION_START_DATE = '06/15/2026'


def sync_schemes_from_dump():
    """
    Hit the full NAV dump, compare against data.json, and:
    - Fix wrong scheme names
    - Auto-add new schemes (so they get backfilled in this same run)
    - Log new and dead schemes to missing_funds.json
    Returns True if data.json was modified.
    """
    data_file = "data/data.json"
    missing_file = "data/missing_funds.json"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://npstrust.org.in/',
    }

    logger.info("Syncing scheme list from full NAV dump...")
    try:
        r = requests.get(DISCOVERY_URL, headers=headers, verify=False, timeout=30)
        if r.status_code != 200 or len(r.content) < 100:
            logger.warning(f"Full dump unavailable (status={r.status_code}), skipping sync")
            return False
        text = r.content.decode('utf-8', errors='ignore')
        df = pd.read_csv(StringIO(text), sep='\t')
    except Exception as e:
        logger.warning(f"Could not fetch full dump: {e}, skipping sync")
        return False

    # Build dump map: scheme_code -> {name, pfm_name, nav, date}
    dump = {}
    for _, row in df.iterrows():
        code = str(row.get('SCHEME ID', '')).strip()
        if not code:
            continue
        dump[code] = {
            'name': str(row.get('SCHEME NAME', '')).strip(),
            'pfm_name': str(row.get('PFM NAME', '')).strip(),
            'nav': str(row.get('NAV VALUE', '')).strip(),
            'date': str(row.get('DATE OF NAV', '')).strip(),
        }

    # Load existing data.json
    try:
        with open(data_file) as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Could not read data.json: {e}")
        return False

    our_map = {d['Scheme Code']: d for d in data}

    new_schemes = []
    name_fixes = 0
    dead_schemes = []

    # Fix name mismatches and collect new schemes
    for code, info in dump.items():
        if code not in our_map:
            # New scheme — derive PFM code from scheme code (SM008025 -> PFM008)
            pfm_code = f"PFM{code[2:5]}"
            # Parse date from dump (YYYY-MM-DD) to our DATE_FORMAT (MM/DD/YYYY)
            try:
                dt = datetime.strptime(info['date'], '%Y-%m-%d')
                formatted_date = dt.strftime(DATE_FORMAT)
            except Exception:
                formatted_date = datetime.now().strftime(DATE_FORMAT)

            new_entry = {
                "Date": formatted_date,
                "PFM Code": pfm_code,
                "PFM Name": info['pfm_name'],
                "Scheme Code": code,
                "Scheme Name": info['name'],
                "NAV": info['nav'],
            }
            data.append(new_entry)
            our_map[code] = new_entry
            new_schemes.append(new_entry)
            logger.info(f"Auto-added new scheme: {code} - {info['name']}")
        else:
            # Fix name if mismatch
            if our_map[code]['Scheme Name'].strip() != info['name']:
                logger.info(f"Fixing name for {code}: '{our_map[code]['Scheme Name']}' -> '{info['name']}'")
                our_map[code]['Scheme Name'] = info['name']
                name_fixes += 1

    # Find dead schemes (in ours but not in dump)
    for code, entry in our_map.items():
        if code not in dump:
            dead_schemes.append({'Scheme Code': code, 'Scheme Name': entry['Scheme Name']})

    modified = new_schemes or name_fixes > 0

    if modified:
        with open(data_file, 'w') as f:
            json.dump(list(our_map.values()), f, indent=4)
        logger.info(f"data.json updated: {len(new_schemes)} new schemes added, {name_fixes} names fixed")

    # Write missing_funds.json
    if new_schemes or dead_schemes:
        missing_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "new_schemes_added": len(new_schemes),
                "name_fixes": name_fixes,
                "dead_schemes_count": len(dead_schemes),
            },
            "new_schemes": new_schemes,
            "dead_schemes": dead_schemes,
        }
        with open(missing_file, 'w') as f:
            json.dump(missing_data, f, indent=4)
        logger.info(f"missing_funds.json updated: {len(new_schemes)} new, {len(dead_schemes)} dead")

    logger.info(f"Sync complete: {len(new_schemes)} new, {name_fixes} name fixes, {len(dead_schemes)} dead")
    return new_schemes

def _get_last_stored_date():
    """Return the most recent date stored across all scheme JSON files."""
    latest = None
    data_dir = 'data'
    for fname in os.listdir(data_dir):
        if not fname.startswith('SM') or not fname.endswith('.json'):
            continue
        try:
            with open(os.path.join(data_dir, fname)) as f:
                d = json.load(f)
            if d:
                first_key = next(iter(d))  # files are sorted newest first
                dt = datetime.strptime(first_key, DATE_FORMAT)
                if latest is None or dt > latest:
                    latest = dt
        except Exception:
            continue
    return latest


def _fetch_protean(dt):
    """Fetch NAV data from Protean ZIP for a specific date. Returns {scheme_code: {nav, date, pfm_name, scheme_name}} or {}."""
    date_str = dt.strftime('%d%m%Y')
    url = PROTEAN_URL.format(date_str=date_str)
    try:
        r = requests.get(url, verify=False, timeout=30)
        if r.status_code != 200 or len(r.content) < 100:
            return {}
        import zipfile as zf
        z = zf.ZipFile(BytesIO(r.content))
        out_file = next(f for f in z.namelist() if f.endswith('.out'))
        lines = z.open(out_file).read().decode('utf-8', errors='ignore').strip().split('\n')
        data = {}
        for line in lines:
            cols = line.strip().split(',')
            if len(cols) == 6:
                sc = cols[3].strip()
                data[sc] = {
                    'nav': str(float(cols[5].strip())),
                    'date': cols[0].strip(),       # already MM/DD/YYYY
                    'pfm_name': cols[2].strip(),
                    'scheme_name': cols[4].strip(),
                }
        return data
    except Exception as e:
        logger.warning(f"Protean fetch failed for {dt.strftime('%d-%m-%Y')}: {e}")
        return {}


def _fetch_nps_trust():
    """Fetch latest NAV data from NPS Trust full dump. Returns {scheme_code: {nav, date, pfm_name, scheme_name}} or {}."""
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://npstrust.org.in/'}
    try:
        r = requests.get(DISCOVERY_URL, headers=headers, verify=False, timeout=30)
        if r.status_code != 200 or len(r.content) < 100:
            return {}
        df = pd.read_csv(StringIO(r.content.decode('utf-8', errors='ignore')), sep='\t')
        data = {}
        for _, row in df.iterrows():
            sc = str(row.get('SCHEME ID', '')).strip()
            nav = str(row.get('NAV VALUE', '')).strip()
            date_raw = str(row.get('DATE OF NAV', '')).strip()
            pfm_name = str(row.get('PFM NAME', '')).strip()
            scheme_name = str(row.get('SCHEME NAME', '')).strip()
            if not sc or not nav:
                continue
            try:
                nav_f = str(float(nav))
                dt = datetime.strptime(date_raw, '%Y-%m-%d')
                formatted_date = dt.strftime(DATE_FORMAT)
                data[sc] = {'nav': nav_f, 'date': formatted_date, 'pfm_name': pfm_name, 'scheme_name': scheme_name}
            except (ValueError, Exception):
                pass
        return data
    except Exception as e:
        logger.warning(f"NPS Trust dump fetch failed: {e}")
        return {}


def fetch_and_fix_from_dump():
    """
    Primary daily NAV fetch using dual-source cross-validation:
    1. Protean ZIP (primary)  — 273 schemes, date-specific, historically correct
    2. NPS Trust full dump (secondary) — 262 schemes, cross-check only

    If both sources agree on a NAV → save with confidence.
    If they disagree → log a warning (Protean value is used; NPS Trust remapping is a known issue).
    Also detects and repairs corrupted entries (stored NAV != source NAV for same date).
    Returns list of records for save_latest_data.
    """
    today = datetime.now()

    # --- Source 1: Protean (fetch ALL missing trading days, not just the latest) ---
    # Find the most recent date we already have across all scheme files
    logger.info("Fetching daily NAVs from Protean...")
    last_stored = _get_last_stored_date()
    protean_by_date = {}  # date_str -> {scheme_code -> info}
    for days_back in range(30):  # scan up to 30 days back
        candidate = today - timedelta(days=days_back)
        if candidate.weekday() >= 5:  # skip weekends
            continue
        if last_stored and candidate <= last_stored:
            break  # already have everything up to here
        result = _fetch_protean(candidate)
        if result:
            protean_by_date[candidate.strftime(DATE_FORMAT)] = result
            logger.info(f"Protean: fetched {len(result)} records for {candidate.strftime('%d-%m-%Y')}")
        else:
            logger.debug(f"Protean: no file for {candidate.strftime('%d-%m-%Y')}")

    # Flatten to most recent date for cross-validation (NPS Trust only has today)
    if protean_by_date:
        latest_protean_date = max(protean_by_date.keys(), key=lambda d: datetime.strptime(d, DATE_FORMAT))
        protean = protean_by_date[latest_protean_date]
    else:
        protean = {}
        logger.warning("Protean: no data found in last 30 days")

    # --- Source 2: NPS Trust full dump ---
    logger.info("Fetching daily NAVs from NPS Trust full dump...")
    nps = _fetch_nps_trust()

    if not protean and not nps:
        logger.error("Both sources unavailable — skipping daily fetch")
        sys.exit(2)

    # --- Cross-validate ---
    mismatches = []
    for sc in set(protean) & set(nps):
        p_nav, n_nav = protean[sc]['nav'], nps[sc]['nav']
        if abs(float(p_nav) - float(n_nav)) > 0.0001:
            mismatches.append((sc, p_nav, n_nav))

    if protean and nps:
        if mismatches:
            logger.warning(f"NAV mismatch between Protean and NPS Trust for {len(mismatches)} schemes:")
            for sc, p, n in mismatches:
                logger.warning(f"  {sc}: Protean={p}, NPS Trust={n} — using Protean value")
        else:
            logger.info(f"Cross-validation passed: {len(set(protean) & set(nps))} schemes match perfectly")
    elif not protean:
        logger.info("Protean unavailable — using NPS Trust as sole source (no cross-validation)")
    elif not nps:
        logger.info("NPS Trust unavailable — using Protean as sole source (no cross-validation)")

    # Build list of (date, scheme_data) to save — all Protean dates + NPS Trust for latest
    # NPS Trust fills in schemes not in Protean for the latest date only
    dates_to_save = {}  # date_str -> {scheme_code -> info}
    for date_str, schemes in protean_by_date.items():
        dates_to_save[date_str] = dict(schemes)
    # Merge NPS Trust into latest date (covers schemes Protean dropped)
    if nps:
        latest_nps_date = next(iter(nps.values()))['date']
        if latest_nps_date not in dates_to_save:
            dates_to_save[latest_nps_date] = {}
        for sc, info in nps.items():
            if sc not in dates_to_save[latest_nps_date]:
                dates_to_save[latest_nps_date][sc] = info  # NPS only for schemes not in Protean
    if not dates_to_save:
        logger.warning("No data from either source — nothing to save")
        return []

    # --- Save to scheme JSON files ---
    new_records = []
    fixes = 0
    corruption_cutoff = datetime.strptime(CORRUPTION_START_DATE, DATE_FORMAT)

    for date_str, schemes in sorted(dates_to_save.items(), key=lambda x: datetime.strptime(x[0], DATE_FORMAT)):
        for scheme_code, info in schemes.items():
            nav_val = info['nav']
            formatted_date = info.get('date') or date_str

            if not formatted_date:
                continue

            pfm_code = f"PFM{scheme_code[2:5]}"
            scheme_file = os.path.join('data', f"{scheme_code}.json")

            if os.path.exists(scheme_file):
                try:
                    with open(scheme_file, 'r') as f:
                        scheme_data = json.load(f, object_pairs_hook=OrderedDict)
                except Exception:
                    scheme_data = OrderedDict()
            else:
                scheme_data = OrderedDict()

            if formatted_date in scheme_data:
                if scheme_data[formatted_date] == nav_val:
                    continue  # Already correct

                # Wrong value — remove corrupted entries from cutoff date onwards
                corrupted = [d for d in list(scheme_data.keys())
                             if datetime.strptime(d, DATE_FORMAT) >= corruption_cutoff]
                for d in corrupted:
                    del scheme_data[d]
                logger.info(f"Fixed {scheme_code}: removed {len(corrupted)} corrupted entries (>= {CORRUPTION_START_DATE})")
                fixes += 1

            scheme_data[formatted_date] = nav_val
            sorted_data = OrderedDict(
                sorted(scheme_data.items(), key=lambda x: datetime.strptime(x[0], DATE_FORMAT), reverse=True)
            )
            with open(scheme_file, 'w') as f:
                json.dump(sorted_data, f, indent=4)

            new_records.append({
                "Date": formatted_date,
                "PFM Code": pfm_code,
                "PFM Name": info.get('pfm_name', ''),
                "Scheme Code": scheme_code,
                "Scheme Name": info.get('scheme_name', ''),
                "NAV": nav_val,
            })

    logger.info(f"Daily fetch complete: {len(new_records)} records saved, {fixes} fixes, {len(mismatches)} source mismatches")
    return new_records


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

def get_existing_dates(scheme_code):
    """Get a set of all dates already present for a specific scheme"""
    scheme_file = os.path.join('data', f"{scheme_code}.json")
    existing_dates = set()
    
    if os.path.exists(scheme_file):
        try:
            with open(scheme_file, 'r') as f:
                scheme_data = json.load(f)
            if scheme_data:
                # Convert string dates to datetime objects for comparison
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
        
        # Get existing dates to prevent duplicates but allow backfill
        existing_dates = get_existing_dates(scheme_code)
        
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
                
                # FIX: Check if we specifically have this date, rather than if it's older than the latest
                # This allows backfilling of missing historical dates
                if current_date in existing_dates:
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
                
                # Add to set to prevent duplicates within the same run/file
                existing_dates.add(current_date)
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

    # Step 1: Sync scheme list — fix names, auto-add new schemes, log dead ones
    new_schemes = sync_schemes_from_dump()

    # Step 2: Fetch today's NAVs from full dump (1 request, correct for all schemes)
    # Also repairs any corrupted entries caused by per-scheme endpoint remapping
    daily_records = fetch_and_fix_from_dump()

    if daily_records:
        save_latest_data(daily_records)
        logger.info(f"Saved {len(daily_records)} daily NAV records")

    # Step 3: Backfill history for newly discovered schemes via per-scheme endpoint
    backfill_data = []
    if new_schemes:
        pfm_scheme_mappings, pfm_names, scheme_names = get_pfm_scheme_mappings()
        logger.info(f"Backfilling history for {len(new_schemes)} new schemes...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_scheme = {
                executor.submit(process_scheme, s['PFM Code'], s['Scheme Code'], pfm_names, scheme_names): s
                for s in new_schemes
            }
            for future in concurrent.futures.as_completed(future_to_scheme):
                s = future_to_scheme[future]
                try:
                    data = future.result()
                    backfill_data.extend(data)
                except Exception as exc:
                    logger.error(f"Backfill error for {s['Scheme Code']}: {exc}")

        if backfill_data:
            update_scheme_json(backfill_data)
            save_latest_data(backfill_data)
            logger.info(f"Backfilled {len(backfill_data)} historical records for {len(new_schemes)} new schemes")

    total = len(daily_records) + len(backfill_data)
    if total:
        logger.info(f"Script completed successfully. Total records processed: {total}")
    else:
        logger.info("No new data available. Files remain unchanged.")