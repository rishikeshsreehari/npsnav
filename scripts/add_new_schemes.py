"""
Script to add new DIRECT and GS scheme variants to data.json
Based on the Multiple NAV Framework introduced April 1, 2026
"""

import json
from datetime import datetime

# New schemes identified from the April 10, 2026 NAV dump
NEW_SCHEMES = [
    # SBI (PFM001) - GS and DIRECT variants
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001022", "Scheme Name": "NPS TRUST A/C SBI PENSION FUND SCHEME E - TIER I GS"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001025", "Scheme Name": "NPS TRUST A/C SBI PENSION FUND SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001023", "Scheme Name": "NPS TRUST A/C SBI PENSION FUND SCHEME C - TIER I GS"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001026", "Scheme Name": "NPS TRUST A/C SBI PENSION FUND SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001024", "Scheme Name": "NPS TRUST A/C SBI PENSION FUND SCHEME G - TIER I GS"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001027", "Scheme Name": "NPS TRUST A/C SBI PENSION FUND SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001028", "Scheme Name": "NPS TRUST A/C SBI PENSION FUND SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001029", "Scheme Name": "NPS TRUST A/C SBI PENSION FUND SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001030", "Scheme Name": "NPS TRUST A/C SBI PENSION FUND SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001031", "Scheme Name": "NPS TRUST - A/C SBI PENSION FUNDS - NPS VATSALYA SCHEME POP"},
    {"PFM Code": "PFM001", "PFM Name": "SBI Pension Funds Pvt. Ltd.", "Scheme Code": "SM001032", "Scheme Name": "NPS TRUST A/C-SBI PENSION FUNDS PRIVATE LIMITED- NPS LITE SCHEME - GOVT. PATTERN DIRECT"},

    # UTI (PFM002)
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002024", "Scheme Name": "NPS TRUST A/C - UTI PENSION FUND SCHEME E - TIER I GS"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002025", "Scheme Name": "NPS TRUST A/C - UTI PENSION FUND SCHEME C - TIER I GS"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002026", "Scheme Name": "NPS TRUST A/C - UTI PENSION FUND SCHEME G - TIER I GS"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002027", "Scheme Name": "NPS TRUST A/C - UTI PENSION FUND SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002028", "Scheme Name": "NPS TRUST A/C - UTI PENSION FUND SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002029", "Scheme Name": "NPS TRUST A/C - UTI PENSION FUND SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002030", "Scheme Name": "NPS TRUST- A/C - UTI PENSION FUND SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002031", "Scheme Name": "NPS TRUST- A/C - UTI PENSION FUND SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002032", "Scheme Name": "NPS TRUST- A/C - UTI PENSION FUND SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002033", "Scheme Name": "NPS TRUST - A/C UTI PENSION FUND - NPS VATSALYA SCHEME POP"},
    {"PFM Code": "PFM002", "PFM Name": "UTI Pension Fund Limited.", "Scheme Code": "SM002034", "Scheme Name": "NPS TRUST- A/C - UTI PENSION FUND - NPS LITE SCHEME GOVT. PATTERN DIRECT"},

    # LIC (PFM003)
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003022", "Scheme Name": "NPS TRUST A/C LIC PENSION FUND SCHEME E - TIER I GS"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003023", "Scheme Name": "NPS TRUST A/C LIC PENSION FUND SCHEME C - TIER I GS"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003024", "Scheme Name": "NPS TRUST A/C LIC PENSION FUND SCHEME G - TIER I GS"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003025", "Scheme Name": "NPS TRUST A/C LIC PENSION FUND SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003026", "Scheme Name": "NPS TRUST A/C LIC PENSION FUND SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003027", "Scheme Name": "NPS TRUST A/C LIC PENSION FUND SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003028", "Scheme Name": "NPS TRUST A/C LIC PENSION FUND SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003029", "Scheme Name": "NPS TRUST A/C LIC PENSION FUND SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003030", "Scheme Name": "NPS TRUST A/C LIC PENSION FUND SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003031", "Scheme Name": "NPS TRUST - A/C LIC PENSION FUND - NPS VATSALYA SCHEME POP"},
    {"PFM Code": "PFM003", "PFM Name": "LIC Pension Fund Ltd.", "Scheme Code": "SM003032", "Scheme Name": "NPS TRUST A/C-LIC PENSION FUND LIMITED- NPS LITE SCHEME - GOVT. PATTERN DIRECT"},

    # Kotak (PFM005)
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005013", "Scheme Name": "NPS TRUST A/C KOTAK PENSION FUND SCHEME E - TIER I GS"},
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005014", "Scheme Name": "NPS TRUST A/C KOTAK PENSION FUND SCHEME C - TIER I GS"},
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005015", "Scheme Name": "NPS TRUST A/C KOTAK PENSION FUND SCHEME G - TIER I GS"},
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005016", "Scheme Name": "NPS TRUST A/C KOTAK PENSION FUND SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005017", "Scheme Name": "NPS TRUST A/C KOTAK PENSION FUND SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005018", "Scheme Name": "NPS TRUST A/C KOTAK PENSION FUND SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005019", "Scheme Name": "NPS TRUST A/C KOTAK PENSION FUND SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005020", "Scheme Name": "NPS TRUST A/C KOTAK PENSION FUND SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005021", "Scheme Name": "NPS TRUST A/C KOTAK PENSION FUND SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM005", "PFM Name": "Kotak Mahindra Pension Fund Ltd.", "Scheme Code": "SM005022", "Scheme Name": "NPS TRUST - A/C KOTAK MAHINDRA PENSION FUND - NPS VATSALYA SCHEME POP"},

    # ICICI (PFM007)
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007015", "Scheme Name": "NPS TRUST A/C ICICI PRUDENTIAL PENSION FUND SCHEME E - TIER I GS"},
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007016", "Scheme Name": "NPS TRUST A/C ICICI PRUDENTIAL PENSION FUND  SCHEME C - TIER I GS"},
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007017", "Scheme Name": "NPS TRUST A/C ICICI PRUDENTIAL PENSION FUND  SCHEME G - TIER I GS"},
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007018", "Scheme Name": "NPS TRUST A/C ICICI PRUDENTIAL PENSION FUND SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007019", "Scheme Name": "NPS TRUST A/C ICICI PRUDENTIAL PENSION FUND  SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007020", "Scheme Name": "NPS TRUST A/C ICICI PRUDENTIAL PENSION FUND  SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007021", "Scheme Name": "NPS TRUST A/C ICICI PRUDENTIAL PENSION FUND SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007022", "Scheme Name": "NPS TRUST A/C ICICI PRUDENTIAL PENSION FUND SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007023", "Scheme Name": "NPS TRUST A/C ICICI PRUDENTIAL PENSION FUND SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM007", "PFM Name": "ICICI Prudential Pension Fund Management Co. Ltd.", "Scheme Code": "SM007024", "Scheme Name": "NPS TRUST - A/C ICICI PRUDENTIAL PENSION FUND - NPS VATSALYA SCHEME POP"},

    # HDFC (PFM008)
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008015", "Scheme Name": "NPS TRUST A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME E - TIER I GS"},
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008016", "Scheme Name": "NPS TRUST A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME C - TIER I GS"},
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008017", "Scheme Name": "NPS TRUST A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME G - TIER I GS"},
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008018", "Scheme Name": "NPS TRUST A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008019", "Scheme Name": "NPS TRUST A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008020", "Scheme Name": "NPS TRUST A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008021", "Scheme Name": "NPS TRUST- A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008022", "Scheme Name": "NPS TRUST- A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008023", "Scheme Name": "NPS TRUST- A/C HDFC PENSION FUND MANAGEMENT LIMITED SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM008", "PFM Name": "HDFC Pension Fund Management Limited", "Scheme Code": "SM008024", "Scheme Name": "NPS TRUST - A/C HDFC PENSION FUND - NPS VATSALYA SCHEME POP"},

    # ABSL (PFM010)
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010013", "Scheme Name": "NPS TRUST A/C ADITYA BIRLA SUNLIFE PENSION FUND SCHEME E - TIER I GS"},
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010014", "Scheme Name": "NPS TRUST A/C ADITYA BIRLA SUNLIFE PENSION FUND SCHEME C - TIER I GS"},
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010015", "Scheme Name": "NPS TRUST A/C ADITYA BIRLA SUNLIFE PENSION FUND SCHEME G - TIER I GS"},
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010016", "Scheme Name": "NPS TRUST A/C ADITYA BIRLA SUNLIFE PENSION FUND SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010017", "Scheme Name": "NPS TRUST A/C ADITYA BIRLA SUNLIFE PENSION FUND SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010018", "Scheme Name": "NPS TRUST A/C ADITYA BIRLA SUNLIFE PENSION FUND SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010019", "Scheme Name": "NPS TRUST A/C ADITYA BIRLA SUNLIFE PENSION FUND SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010020", "Scheme Name": "NPS TRUST A/C ADITYA BIRLA SUNLIFE PENSION FUND SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010021", "Scheme Name": "NPS TRUST A/C ADITYA BIRLA SUNLIFE PENSION FUND SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM010", "PFM Name": "Aditya Birla Sunlife Pension Fund management Limited", "Scheme Code": "SM010022", "Scheme Name": "NPS TRUST - A/C ADITYA BIRLA SUNLIFE PENSION FUND - NPS VATSALYA SCHEME POP"},

    # Tata (PFM011)
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011011", "Scheme Name": "NPS TRUST A/C TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME E - TIER I GS"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011012", "Scheme Name": "NPS TRUST A/C TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME C - TIER I GS"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011013", "Scheme Name": "NPS TRUST A/C TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME G - TIER I GS"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011014", "Scheme Name": "NPS TRUST A/C TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011015", "Scheme Name": "NPS TRUST A/C TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011016", "Scheme Name": "NPS TRUST A/C TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011017", "Scheme Name": "NPS TRUST A/C TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011018", "Scheme Name": "NPS TRUST A/C TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011019", "Scheme Name": "NPS TRUST A/C TATA PENSION FUND MANAGEMENT PRIVATE LIMITED SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011020", "Scheme Name": "NPS TRUST - A/C TATA PENSION FUND - NPS VATSALYA SCHEME POP"},
    {"PFM Code": "PFM011", "PFM Name": "Tata Pension Fund Management Private Limited", "Scheme Code": "SM011021", "Scheme Name": "NPS TRUST A/C - TATA PENSION NPS SWASTHYA FUND"},

    # Axis (PFM013)
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013011", "Scheme Name": "NPS TRUST A/C AXIS PENSION FUND MANAGEMENT LIMITED SCHEME E - TIER I GS"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013012", "Scheme Name": "NPS TRUST A/C AXIS PENSION FUND MANAGEMENT LIMITED SCHEME C - TIER I GS"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013013", "Scheme Name": "NPS TRUST A/C AXIS PENSION FUND MANAGEMENT LIMITED SCHEME G - TIER I GS"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013014", "Scheme Name": "NPS TRUST A/C AXIS PENSION FUND MANAGEMENT LIMITED SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013015", "Scheme Name": "NPS TRUST A/C AXIS PENSION FUND MANAGEMENT LIMITED SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013016", "Scheme Name": "NPS TRUST A/C AXIS PENSION FUND MANAGEMENT LIMITED SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013017", "Scheme Name": "NPS TRUST A/C AXIS PENSION FUND MANAGEMENT LIMITED SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013018", "Scheme Name": "NPS TRUST A/C AXIS PENSION FUND MANAGEMENT LIMITED SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013019", "Scheme Name": "NPS TRUST A/C AXIS PENSION FUND MANAGEMENT LIMITED SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013020", "Scheme Name": "NPS TRUST - A/C AXIS PENSION FUND - NPS VATSALYA SCHEME POP"},
    {"PFM Code": "PFM013", "PFM Name": "AXIS PENSION FUND MANAGEMENT LIMITED", "Scheme Code": "SM013021", "Scheme Name": "NPS TRUST - A/C AXIS NPS SWASTHYA TOP-UP PLUS"},

    # DSP (PFM014)
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014011", "Scheme Name": "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME E - TIER I GS"},
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014012", "Scheme Name": "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME C - TIER I GS"},
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014013", "Scheme Name": "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME G - TIER I GS"},
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014014", "Scheme Name": "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME E - TIER I DIRECT"},
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014015", "Scheme Name": "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME C - TIER I DIRECT"},
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014016", "Scheme Name": "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME G - TIER I DIRECT"},
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014017", "Scheme Name": "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME E - TIER II DIRECT"},
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014018", "Scheme Name": "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME C - TIER II DIRECT"},
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014019", "Scheme Name": "NPS TRUST A/C DSP PENSION FUND MANAGERS PRIVATE LIMITED SCHEME G - TIER II DIRECT"},
    {"PFM Code": "PFM014", "PFM Name": "DSP PENSION FUND MANAGERS PRIVATE LIMITED", "Scheme Code": "SM014020", "Scheme Name": "NPS TRUST - A/C DSP PENSION FUND - NPS VATSALYA SCHEME POP"},
]

def main():
    print("🚀 Adding new DIRECT and GS scheme variants to data.json...")
    print(f"📊 Found {len(NEW_SCHEMES)} new schemes to add\n")

    # Load existing data.json
    with open('data/data.json', 'r') as f:
        existing_data = json.load(f)

    print(f"📁 Current schemes in data.json: {len(existing_data)}")

    # Get existing scheme codes to avoid duplicates
    existing_codes = {fund['Scheme Code'] for fund in existing_data}

    # Add new schemes
    added_count = 0
    skipped_count = 0

    for scheme in NEW_SCHEMES:
        if scheme['Scheme Code'] in existing_codes:
            print(f"⏭️  Skipping {scheme['Scheme Code']} (already exists)")
            skipped_count += 1
            continue

        # Create new fund entry with placeholder NAV
        new_fund = {
            "Date": "04/01/2026",  # April 1, 2026 - when Multiple NAV Framework started
            "PFM Code": scheme['PFM Code'],
            "PFM Name": scheme['PFM Name'],
            "Scheme Code": scheme['Scheme Code'],
            "Scheme Name": scheme['Scheme Name'],
            "NAV": "10.0000"  # Placeholder - will be updated by fetch.py
        }

        existing_data.append(new_fund)
        print(f"✅ Added: {scheme['Scheme Code']} - {scheme['Scheme Name'][:60]}...")
        added_count += 1

    # Save updated data.json
    with open('data/data.json', 'w') as f:
        json.dump(existing_data, f, indent=4)

    print(f"\n{'='*80}")
    print(f"✅ Successfully added {added_count} new schemes")
    print(f"⏭️  Skipped {skipped_count} existing schemes")
    print(f"📊 Total schemes now: {len(existing_data)}")
    print(f"{'='*80}")
    print("\n🔄 Next steps:")
    print("1. Run: python scripts/fetch.py")
    print("   (This will download real NAV data from April 1, 2026 onwards)")
    print("2. Run: make build")
    print("   (This will regenerate the site with new schemes)")
    print("3. Test locally: make serve")
    print("4. Deploy: git add, commit, push")

if __name__ == "__main__":
    main()
