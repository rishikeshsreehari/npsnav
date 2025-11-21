import os
import shutil
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Initialize Jinja2 environment
def init_jinja_env():
    return Environment(loader=FileSystemLoader('src/templates'))

# Load the base data.json file
def load_base_data():
    with open('data/data.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Load the changelog data
def load_changelog():
    try:
        with open('data/changelog.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading changelog: {e}")
        return []

# Helper function to handle null values and format NAV with two decimal places
def format_value(value):
    if value is None or value == "null":
        return '-'
    return f'{float(value):.2f}%'

# Helper function to format NAV with two decimal places without a percentage symbol
def format_nav(nav):
    if nav is None or nav == "null":
        return '-'
    return f'{float(nav):.2f}'

# Convert date from mm/dd/yyyy to dd-mm-yyyy format
def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%d-%m-%Y")
    except ValueError:
        return date_str

# Normalize PFM names to handle variations
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

# Generate table rows for all funds
def generate_table_rows(funds):
    rows = ""
    pfm_names = set()
    
    for fund in funds:
        scheme_name = fund['Scheme Name']
        scheme_code = fund['Scheme Code']
        raw_pfm_name = fund.get('PFM Name', '')
        pfm_name = normalize_pfm_name(raw_pfm_name)
        nav_value = fund['NAV']
        nav = format_nav(nav_value)
        
        if pfm_name:
            pfm_names.add(pfm_name)
        
        row = f'''
        <tr data-pfm="{pfm_name}">
            <td><a href="funds/{scheme_code}">{scheme_name}</a></td>
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
                    # Handle cases where value is not a valid number
                    css_class = 'null'
            
            # Append the table cell with the appropriate CSS class
            row += f'<td class="{css_class}">{formatted_value}</td>'
        
        row += '</tr>'
        rows += row
        
    return rows, sorted(list(pfm_names))

# Render all HTML files in the content directory
def render_html_files(env, funds, latest_version, changelog):
    table_rows, pfm_options = generate_table_rows(funds)
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
        VERSION=latest_version  # Add this line to pass the version
    )
    
    # Save the rendered content to the public directory
    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.write(rendered_content)
    
    print(f'Changelog page generated at {output_path}')

# Copy files to public directory
def copy_files():
    # Check and copy assets directory
    if os.path.exists('assets'):
        shutil.copytree('assets', 'public/assets', dirs_exist_ok=True)
        print("Assets have been copied.")
    
    # Check and copy the _redirects file
    if os.path.exists('_redirects'):
        shutil.copy('_redirects', 'public/_redirects')
        print("_redirects file has been copied.")

# Main function to orchestrate the build process
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