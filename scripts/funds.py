import json
import os
import re
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

# Inline chart data covers this window; older data is lazy-fetched from the historical API on demand
INLINE_WINDOW_DAYS = 370

def format_display_date(date_str):
    """Convert the stored MM/DD/YYYY date to DD-MM-YYYY for display."""
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%d-%m-%Y")
    except (TypeError, ValueError):
        return date_str

def shorten_scheme_name(name):
    """Remove verbose prefixes and company name suffixes from scheme names."""
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

# Load the templates
env = Environment(loader=FileSystemLoader('src/templates'))

# main.py runs earlier in the build and writes this cache after fetching from GitHub;
# reuse it here instead of hitting the API again
try:
    with open('data/github_stars.json', 'r') as f:
        env.globals['GITHUB_STARS'] = json.load(f)['count']
except (FileNotFoundError, KeyError, ValueError):
    env.globals['GITHUB_STARS'] = None

template = env.get_template('funds.html')

# Load the data.json file
with open('data/data.json', 'r') as f:
    funds_data = json.load(f)

# Function to load Nifty data
def load_nifty_data():
    try:
        with open('data/nifty.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: nifty.json not found")
        return {}

# Load Nifty data once
nifty_data = load_nifty_data()

# Directory for generated HTML files
output_dir = 'public/funds'
os.makedirs(output_dir, exist_ok=True)

# Loop through each fund in data.json
for fund in funds_data:
    scheme_code = fund['Scheme Code']
    scheme_name = shorten_scheme_name(fund['Scheme Name']).upper()
    pfm_name = fund['PFM Name']
    current_nav = round(float(fund['NAV']), 2)
    nav_date = format_display_date(fund['Date'])
    
    print(f"Processing fund: {scheme_name} (Scheme Code: {scheme_code})")
    
    # Load the individual fund JSON for historic NAVs
    nav_file = f'data/{scheme_code}.json'
    
    # ADD THIS SAFETY CHECK
    if not os.path.exists(nav_file):
        print(f"Warning: {nav_file} not found. Skipping {scheme_name}")
        continue
    
    with open(nav_file, 'r') as nav_f:
        historical_navs = json.load(nav_f)

    # Skip if historical data is empty
    if not historical_navs:
        print(f"Warning: No historical data for {scheme_name}. Skipping.")
        continue

    # True first/last dates require chronological (not lexicographic) comparison,
    # since keys spanning multiple years don't sort correctly as mm/dd/yyyy strings
    parsed_dates = {date: datetime.strptime(date, "%m/%d/%Y") for date in historical_navs}
    first_date = min(parsed_dates, key=parsed_dates.get)
    last_date = max(parsed_dates, key=parsed_dates.get)
    cutoff = parsed_dates[last_date] - timedelta(days=INLINE_WINDOW_DAYS)

    # Only inline a recent window for fast initial chart render; full history is
    # fetched lazily from /api/historical/{scheme_code}.json for longer timeframes
    nav_data = [
        {"date": date, "nav": nav}
        for date, nav in historical_navs.items()
        if parsed_dates[date] >= cutoff
    ]

    nifty_nav_data = [
        {"date": date, "nav": nav}
        for date, nav in nifty_data.items()
        if datetime.strptime(date, "%m/%d/%Y") >= cutoff
    ]
    
    rendered_html = template.render(
        scheme_name=scheme_name,
        pfm_name=pfm_name,
        current_nav=current_nav,
        nav_date=nav_date,
        nav_data=nav_data,
        nifty_data=nifty_nav_data,  # Added Nifty data
        returns={
            "1M": fund["1M"],
            "3M": fund["3M"],
            "6M": fund["6M"],
            "1Y": fund["1Y"],
            "3Y": fund["3Y"],
            "5Y": fund["5Y"]
        },
        first_date=first_date,
        last_date=last_date,
        scheme_code=scheme_code  # scheme_code for canonical
    )
    
    # Write the rendered HTML to a file with UTF-8 encoding
    output_path = os.path.join(output_dir, f'{scheme_code}.html')
    with open(output_path, 'w', encoding='utf-8') as output_f:
        output_f.write(rendered_html)

print("Fund pages generated successfully.")
