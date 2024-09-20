import json
import os
from jinja2 import Environment, FileSystemLoader

# Load the templates
env = Environment(loader=FileSystemLoader('src/templates'))
template = env.get_template('funds.html')

# Load the data.json file
with open('data/data.json', 'r') as f:
    funds_data = json.load(f)

# Directory for generated HTML files
output_dir = 'public/funds'
os.makedirs(output_dir, exist_ok=True)

# Loop through each fund in data.json
for fund in funds_data:
    scheme_code = fund['Scheme Code']
    scheme_name = fund['Scheme Name'].upper()
    pfm_name = fund['PFM Name']
    current_nav = round(float(fund['NAV']), 2)
    nav_date = fund['Date']
    
    print(f"Processing fund: {scheme_name} (Scheme Code: {scheme_code})")

    # Load the individual fund JSON for historic NAVs
    nav_file = f'data/{scheme_code}.json'
    with open(nav_file, 'r') as nav_f:
        historical_navs = json.load(nav_f)
        
    

    # Transform the nav_data into an array of objects
    nav_data = [{"date": date, "nav": nav} for date, nav in historical_navs.items()]
    
    first_date = min(historical_navs.keys())
    last_date = max(historical_navs.keys())
   
    rendered_html = template.render(
        scheme_name=scheme_name,
        pfm_name=pfm_name,
        current_nav=current_nav,
        nav_date=nav_date,
        nav_data=nav_data,
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
