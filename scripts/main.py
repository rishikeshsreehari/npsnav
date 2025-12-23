import os
import shutil
import json
import re
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


def init_jinja_env():
    return Environment(loader=FileSystemLoader('src/templates'))

# ---------------------------------------------------------
# Data loaders
# ---------------------------------------------------------

def load_base_data():
    with open('data/data.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def load_changelog():
    try:
        with open('data/changelog.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading changelog: {e}")
        return []

# ---------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------

def format_value(value):
    """Handle null values and format % returns to two decimal places."""
    if value is None or value == "null" or value == "":
        return '-'
    return f'{float(value):.2f}%'

def format_nav(nav):
    """Format NAV with two decimal places (no % sign)."""
    if nav is None or nav == "null" or nav == "":
        return '-'
    return f'{float(nav):.2f}'

def convert_date_format(date_str):
    """Convert mm/dd/yyyy to dd-mm-yyyy, else return as-is."""
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%d-%m-%Y")
    except ValueError:
        return date_str

# ---------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------

def normalize_pfm_name(name):
    if not name:
        return ""
    name_upper = name.upper().strip()
    if "SBI" in name_upper:
        return "SBI Pension Funds"
    if "LIC" in name_upper:
        return "LIC Pension Fund"
    if "UTI" in name_upper:
        return "UTI Pension Fund"
    if "HDFC" in name_upper:
        return "HDFC Pension Management"
    if "ICICI" in name_upper:
        return "ICICI Prudential Pension Fund"
    if "KOTAK" in name_upper:
        return "Kotak Mahindra Pension Fund"
    if "ADITYA BIRLA" in name_upper:
        return "Aditya Birla Sun Life Pension Fund"
    if "TATA" in name_upper:
        return "Tata Pension Management"
    if "MAX LIFE" in name_upper:
        return "Max Life Pension Fund"
    if "AXIS" in name_upper:
        return "Axis Pension Fund"
    if "DSP" in name_upper:
        return "DSP Pension Fund Managers"
    return name.strip()

def extract_tier(scheme_name):
    if not scheme_name:
        return ""
    scheme_upper = scheme_name.upper()
    if "TIER II" in scheme_upper or "TIER-II" in scheme_upper or "TIER 2" in scheme_upper:
        return "Tier II"
    elif "TIER I" in scheme_upper or "TIER-I" in scheme_upper or "TIER 1" in scheme_upper:
        return "Tier I"
    return "Unknown"

# ---------------------------------------------------------
# MSF classification (used inside scheme type)
# ---------------------------------------------------------

# List/set of MSF scheme codes – added manually
MSF_SCHEMES = {
    # SBI
    "SM001019",  # SBI NPS JEEVAN SWARNA RETIREMENT YOJANA - LIFE'S GOLDEN PLAN - TIER I
    "SM001020",  # SBI NPS AKSHAY DHARA RETIREMENT YOJANA - HAPPY RETIREMENT PLAN
    
    # UTI
    "SM002019",  # UTI PF WEALTH BUILDER NPS EQUITY SCHEME - TIER I
    "SM002020",  # UTI PF WEALTH BUILDER NPS EQUITY SCHEME - TIER II
    "SM002021",  # UTI PF DYNAMIC ASSET ALLOCATOR NPS SCHEME - TIER I
    "SM002022",  # UTI PF DYNAMIC ASSET ALLOCATOR NPS SCHEME - TIER II
    
    # LIC
    "SM003019",  # LIC PFL NPS SMART BALANCE - TIER I
    "SM003020", # LIC PFL NPS GROWTH PLUS - TIER I
    
    
    # KOTAK
    "SM005011",  # KOTAK NPS KUBER EQUITY FUND - TIER I
    
    # ICICI
    "SM007011",  # ICICI NPS MY FAMILY MY FUTURE (INMFMF) - TIER I
    "SM007012",  # ICICI PF NPS DYNAMIC REALLOCATION ENHANCED ACCUMULATION MODEL PLAN
    
    # HDFC (New Additions)
    "SM008011",  # HDFC PF NPS SURAKSHIT INCOME FUND - TIER I
    "SM008012",  # HDFC PF NPS SURAKSHIT INCOME FUND - TIER II
    "SM008013",  # HDFC PF NPS EQUITY ADVANTAGE FUND - TIER I
    
    # ABSL (New Additions)
    "SM010010",  # ABSLPF SECURE RETIREMENT EQUITY FUND - NPS - TIER I
    "SM010011",  # ABSLPF SECURE FUTURE FUND - NPS - TIER I
    
    # TATA (New Addition)
    "SM011009",  # TATA PENSION FUND NPS SMART RETIREMENT FUND - TIER I
    
    # AXIS (New Addition)
    "SM013009",  # AXIS NPS GOLDEN YEARS FUND - GROWTH - TIER I
    
    # DSP (New Addition)
    "SM014009",  # DSP NPS LONG TERM EQUITY FUND - TIER I
    
    
}

def extract_scheme_type(scheme_name, scheme_code):
    """
    Classify scheme type into specific categories:
    Returns: 'Scheme A', 'Scheme C', 'Scheme E', 'Scheme G', 'MSF', 'Corporate', or 'Others'
    """
    # 1. Check MSF Code first
    if scheme_code in MSF_SCHEMES:
        return "MSF"

    if not scheme_name:
        return "Others"
    
    name_upper = scheme_name.upper()
    
    # 2. Check Corporate (Handles "CORPORATE CG", "CORPORATE-CG", "CORPORATE  CG")
    # Using Regex to handle hyphens and spaces flexibly
    if re.search(r"CORPORATE[\s-]*CG", name_upper):
        return "Corporate"

    # 3. Check Standard Schemes (Handles "SCHEME A", "SCHEME-A")
    if re.search(r"SCHEME[\s-]*A", name_upper):
        return "Scheme A"
    if re.search(r"SCHEME[\s-]*E", name_upper):
        return "Scheme E"
    if re.search(r"SCHEME[\s-]*C", name_upper):
        return "Scheme C"
    if re.search(r"SCHEME[\s-]*G", name_upper):
        return "Scheme G"
    
    # 4. Fallback
    return "Others"

def shorten_scheme_name(name):
    if not name:
        return ""
    
    phrases_to_remove = [
        "PENSION FUND MANAGEMENT COMPANY LIMITED",
        "PENSION FUND MANAGEMENT COMPANY LTD",
        "PENSION FUND MANAGEMENT LIMITED",
        "PENSION FUND MANAGEMENT LTD",
        "PENSION MANAGEMENT COMPANY LIMITED",
        "PENSION MANAGEMENT COMPANY LTD",
        "PENSION FUND MANAGERS PRIVATE LIMITED",
        "PENSION FUND MANAGERS PVT LTD",
        "RETIREMENT SOLUTIONS LIMITED",
        "RETIREMENT SOLUTIONS LTD",
        "RETIREMENT SOLUTIONS",
        "PENSION FUNDS",
        "PENSION FUND",
        "MANAGEMENT LIMITED",
        "MANAGEMENT LTD",
        "COMPANY LIMITED",
        "COMPANY LTD",
        "PRIVATE LIMITED",
        "PVT LTD",
        "LIMITED",
        "LTD"
    ]
    
    cleaned_name = name
    
    # Remove NPS TRUST prefixes first
    nps_pattern = re.compile(r"^NPS TRUST\s*-?\s*A/C\s*-?\s*|^NPS TRUST\s*-?\s*", re.IGNORECASE)
    cleaned_name = nps_pattern.sub("", cleaned_name)

    for phrase in phrases_to_remove:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        cleaned_name = pattern.sub("", cleaned_name)
        
    return " ".join(cleaned_name.split())

# ---------------------------------------------------------
# Scheme type ordering
# ---------------------------------------------------------

SCHEME_TYPE_ORDER = {
    "Scheme A": 1,
    "Scheme C": 2,
    "Scheme E": 3,
    "Scheme G": 4,
    "MSF": 5,
    "Corporate": 6,
    "Others": 7,
}

def sort_scheme_types(types):
    """Sort scheme types in custom order."""
    return sorted(types, key=lambda t: SCHEME_TYPE_ORDER.get(t, 999))

# ---------------------------------------------------------
# Table generation
# ---------------------------------------------------------

def generate_table_rows(funds):
    rows = ""
    pfm_names = set()
    scheme_types = set()
    
    for fund in funds:
        scheme_name = fund['Scheme Name']
        scheme_code = fund['Scheme Code']
        raw_pfm_name = fund.get('PFM Name', '')
        pfm_name = normalize_pfm_name(raw_pfm_name)
        if not pfm_name:
            pfm_name = "Unknown"
            
        tier = extract_tier(scheme_name)
        
        # New robust regex-based extraction
        scheme_type = extract_scheme_type(scheme_name, scheme_code)

        nav_value = fund['NAV']
        nav = format_nav(nav_value)
        
        short_scheme_name = shorten_scheme_name(scheme_name)
        
        if pfm_name:
            pfm_names.add(pfm_name)
        
        if scheme_type:
            scheme_types.add(scheme_type)
        
        # Use the exact 'scheme_type' string for the data attribute
        # This allows the JS filter to work with "Corporate", "Scheme A", etc.
        row = f'''
        <tr data-pfm="{pfm_name}" data-tier="{tier}" data-scheme-type="{scheme_type}">
            <td><a href="funds/{scheme_code}" class="scheme-link" data-full-name="{scheme_name}" data-short-name="{short_scheme_name}">{short_scheme_name}</a></td>
            <td>{nav}</td>
        '''

        # List of periods to iterate over
        periods = ['1D', '7D', '1M', '3M', '6M', '1Y', '3Y', '5Y']
        for period in periods:
            value = fund.get(period)
            formatted_value = format_value(value)
            
            # Determine the CSS class based on the value
            if value is None or value == '':
                css_class = 'null'
            else:
                try:
                    numeric_value = float(value)
                    if numeric_value > 0:
                        css_class = 'positive'
                    elif numeric_value < 0:
                        css_class = 'negative'
                    else:
                        css_class = 'zero'
                except ValueError:
                    css_class = 'null'
            
            row += f'<td class="{css_class}">{formatted_value}</td>'
        
        row += '</tr>'
        rows += row
        
    return rows, sorted(list(pfm_names)), sort_scheme_types(list(scheme_types))

# ---------------------------------------------------------
# Rendering / pages
# ---------------------------------------------------------

def render_html_files(env, funds, latest_version, changelog):
    table_rows, pfm_options, scheme_type_options = generate_table_rows(funds)
    nav_date = convert_date_format(funds[0]['Date']) if funds else "N/A"
    latest_changes = changelog[0] if changelog else None

    for root, dirs, files in os.walk('src/content'):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, 'src/content')
                output_path = os.path.join('public', relative_path)

                # Ensure the output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Load and render the template
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if the file contains Jinja templating
                if '{%' in content or '{{' in content:
                    template = env.from_string(content)
                    rendered_content = template.render(
                        TABLE_ROWS=table_rows, 
                        PFM_OPTIONS=pfm_options,
                        SCHEME_TYPE_OPTIONS=scheme_type_options,
                        NAV_DATE=nav_date,
                        VERSION=latest_version,
                        LATEST_CHANGES=latest_changes
                    )
                else:
                    rendered_content = content

                # Save the rendered file
                with open(output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(rendered_content)
                print(f'Rendered {output_path}')

# Function to generate scheme list page with scheme names and codes
def generate_scheme_list_page(env, funds):
    # Load the scheme list template
    template = env.get_template('nps-funds-list.html')

    # Generate the list of schemes
    schemes = []
    for fund in funds:
        schemes.append({
            'Scheme_Name': fund['Scheme Name'],
            'Scheme_Code': fund['Scheme Code'],
        })

    # Render the page with the list of schemes
    output_path = os.path.join('public', 'nps-funds-list.html')
    rendered_content = template.render(schemes=schemes)

    # Save the rendered content to the public directory
    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.write(rendered_content)

    print(f'Scheme list page generated at {output_path}')

# Function to generate the changelog page
def generate_changelog_page(env, changelog):
    # Load the changelog template
    template = env.get_template('changelog.html')
    
    # Get the latest version for the footer
    latest_version = changelog[0]['version'] if changelog else "v1.0.0"
    
    # Render the page with the changelog data AND the version
    output_path = os.path.join('public', 'changelog.html')
    rendered_content = template.render(
        CHANGELOG=changelog,
        VERSION=latest_version
    )
    
    # Save the rendered content to the public directory
    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.write(rendered_content)
    
    print(f'Changelog page generated at {output_path}')

# ---------------------------------------------------------
# Static assets
# ---------------------------------------------------------

def copy_files():
    # Check and copy assets directory
    if os.path.exists('assets'):
        shutil.copytree('assets', 'public/assets', dirs_exist_ok=True)
        print("Assets have been copied.")
    
    # Check and copy the _redirects file
    if os.path.exists('_redirects'):
        shutil.copy('_redirects', 'public/_redirects')
        print("_redirects file has been copied.")
        
    # Check and copy openapi.json file
    if os.path.exists('openapi.json'):
        shutil.copy('openapi.json', 'public/openapi.json')
        print("openapi.json file has been copied.")

# ---------------------------------------------------------
# Orchestration
# ---------------------------------------------------------

def build_site():
    env = init_jinja_env()
    funds = load_base_data()
    
    # Load the changelog for use in templates
    changelog = load_changelog()
    latest_version = changelog[0]['version'] if changelog else "v1.0.0"
    
    # Render all regular HTML files
    render_html_files(env, funds, latest_version, changelog)
    
    # Generate the scheme list page
    generate_scheme_list_page(env, funds)
    
    # Generate the changelog page
    generate_changelog_page(env, changelog)
    
    # Copy assets to the public directory
    copy_files()

# Execute the build process
if __name__ == "__main__":
    build_site()