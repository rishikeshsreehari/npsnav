
"""
Script to discover new PFM-Scheme combinations from NPS Trust NAV reports
Compares against existing data.json and generates data/missing_funds.json

"""

import requests
import pandas as pd
import os
import json
import time
from io import BytesIO, StringIO
import tempfile
from datetime import datetime
import urllib3
import logging

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://npstrust.org.in/nav-report-excel"

def get_existing_combinations():
    """Get existing PFM-Scheme combinations from data.json"""
    existing = set()
    pfm_codes = set()
    
    data_file = "data/data.json"
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            for record in data:
                pfm_code = record["PFM Code"]
                scheme_code = record["Scheme Code"]
                existing.add((pfm_code, scheme_code))
                pfm_codes.add(pfm_code)
            
            logger.info(f"Loaded {len(existing)} existing combinations from {len(pfm_codes)} PFMs")
            return existing, pfm_codes
            
        except Exception as e:
            logger.error(f"Error reading data.json: {e}")
    
    return set(), set()

def try_read_file_alternative(file_content):
    """Try to read file with different approaches - TSV, CSV, or Excel"""
    
    # Method 1: Try as TSV
    try:
        text_content = file_content.decode('utf-8', errors='ignore')
        if text_content.startswith('ID\t') or 'DATE' in text_content[:100]:
            df = pd.read_csv(StringIO(text_content), sep='\t')
            logger.info("Read as TSV file")
            return df
    except Exception as e:
        logger.debug(f"TSV failed: {e}")
    
    # Method 2: Try as CSV
    try:
        text_content = file_content.decode('utf-8', errors='ignore')
        df = pd.read_csv(StringIO(text_content))
        logger.info("Read as CSV file")
        return df
    except Exception as e:
        logger.debug(f"CSV failed: {e}")
    
    # Method 3: Try xlrd
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
                df = pd.DataFrame(data[1:], columns=data[0] if data else None)
                logger.info("Read with xlrd")
                return df
    except Exception as e:
        logger.debug(f"xlrd failed: {e}")
    
    # Method 4: Try openpyxl
    try:
        df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
        logger.info("Read with openpyxl")
        return df
    except Exception as e:
        logger.debug(f"openpyxl failed: {e}")
    
    # Method 5: Try calamine
    try:
        df = pd.read_excel(BytesIO(file_content), engine='calamine')
        logger.info("Read with calamine")
        return df
    except Exception as e:
        logger.debug(f"calamine failed: {e}")
    
    raise Exception("All file reading methods failed")

def download_all_nav_data():
    """Download the complete NAV report which has ALL funds"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/plain,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://npstrust.org.in/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    try:
        logger.info(f"Downloading complete NAV report from {BASE_URL}...")
        response = requests.get(BASE_URL, headers=headers, verify=False, timeout=30)
        
        if response.status_code == 200 and len(response.content) > 100:
            logger.info(f"Got response: {len(response.content)} bytes")
            df = try_read_file_alternative(response.content)
            
            if df is not None and not df.empty and len(df) > 10:
                logger.info(f"Successfully parsed {len(df)} rows")
                return df
        
        raise Exception(f"Failed to download: status={response.status_code}, size={len(response.content)}")
                
    except Exception as e:
        raise Exception(f"Error downloading NAV report: {e}")

def extract_funds_from_dataframe(df):
    """Extract all unique PFM-Scheme combinations from the dataframe"""
    funds = []
    
    # Based on your sample, columns are:
    # ID, DATE OF NAV, PFM NAME, SCHEME ID, SCHEME NAME, NAV VALUE
    # So: 0=ID, 1=Date, 2=PFM Name, 3=Scheme ID, 4=Scheme Name, 5=NAV
    
    # But let's also try to find them dynamically
    pfm_name_col = None
    scheme_id_col = None
    scheme_name_col = None
    
    for i, col in enumerate(df.columns):
        col_str = str(col).lower().strip()
        if 'pfm' in col_str and 'name' in col_str:
            pfm_name_col = i
        elif 'scheme' in col_str and 'id' in col_str:
            scheme_id_col = i
        elif 'scheme' in col_str and 'name' in col_str:
            scheme_name_col = i
    
    # Fallback to positions based on your sample
    if pfm_name_col is None:
        pfm_name_col = 2
    if scheme_id_col is None:
        scheme_id_col = 3
    if scheme_name_col is None:
        scheme_name_col = 4
    
    logger.info(f"Using columns: PFM Name={pfm_name_col}, Scheme ID={scheme_id_col}, Scheme Name={scheme_name_col}")
    logger.info(f"Column names: {list(df.columns)}")
    
    seen = set()
    
    for index, row in df.iterrows():
        try:
            if len(row) <= max(pfm_name_col, scheme_id_col, scheme_name_col):
                continue
            
            pfm_name = str(row.iloc[pfm_name_col]).strip() if not pd.isna(row.iloc[pfm_name_col]) else None
            scheme_code = str(row.iloc[scheme_id_col]).strip() if not pd.isna(row.iloc[scheme_id_col]) else None
            scheme_name = str(row.iloc[scheme_name_col]).strip() if not pd.isna(row.iloc[scheme_name_col]) else None
            
            # Extract PFM code from scheme code (SM001001 -> PFM001)
            pfm_code = None
            if scheme_code and scheme_code.startswith('SM') and len(scheme_code) >= 6:
                pfm_num = scheme_code[2:5]  # Get 001 from SM001001
                pfm_code = f"PFM{pfm_num}"
            
            if pfm_code and scheme_code and pfm_name and scheme_name:
                key = (pfm_code, scheme_code)
                if key not in seen:
                    seen.add(key)
                    funds.append({
                        'PFM Code': pfm_code,
                        'PFM Name': pfm_name,
                        'Scheme Code': scheme_code,
                        'Scheme Name': scheme_name
                    })
        except Exception as e:
            logger.debug(f"Error processing row {index}: {e}")
            continue
    
    logger.info(f"Extracted {len(funds)} unique PFM-Scheme combinations")
    return funds

if __name__ == "__main__":
    logger.info("Starting fund discovery...")
    
    # Get existing combinations
    existing, pfm_codes = get_existing_combinations()
    logger.info(f"You have {len(existing)} existing combinations in data.json")
    
    # Download the complete NAV report (has ALL funds)
    try:
        df = download_all_nav_data()
    except Exception as e:
        logger.error(f"Failed to download: {e}")
        exit(1)
    
    # Extract all funds
    all_funds = extract_funds_from_dataframe(df)
    logger.info(f"Found {len(all_funds)} total fund combinations")
    
    # Find new funds
    new_funds = []
    for fund in all_funds:
        key = (fund['PFM Code'], fund['Scheme Code'])
        if key not in existing:
            new_funds.append(fund)
            logger.info(f"NEW: {fund['PFM Code']}/{fund['Scheme Code']} - {fund['PFM Name']} / {fund['Scheme Name']}")
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_funds_found": len(all_funds),
            "existing_in_your_data": len(existing),
            "new_combinations_count": len(new_funds)
        },
        "new_combinations": new_funds
    }
    
    # Print summary
    print("\n" + "="*70)
    print("FUND DISCOVERY REPORT")
    print("="*70)
    print(f"Total fund combinations found: {len(all_funds)}")
    print(f"Funds in your data.json:       {len(existing)}")
    print(f"NEW funds found:               {len(new_funds)}")
    
    if new_funds:
        # Save report only if new funds found
        with open('data/missing_funds.json', 'w') as f:
            json.dump(report, f, indent=4)
        
        print("\nNEW FUNDS:")
        for fund in new_funds:
            print(f"  • {fund['PFM Code']}/{fund['Scheme Code']}")
            print(f"    {fund['PFM Name']}")
            print(f"    {fund['Scheme Name']}")
        
        print(f"\n✓ Report saved to: data/missing_funds.json")
        print("✓ Next step: Add these funds to data.json, then run fetch_nav.py")
    else:
        print("\n✓ No new funds found - you're up to date!")
    
    print("="*70 + "\n")