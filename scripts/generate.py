import json
from datetime import datetime

# Load the base data.json file
def load_base_data():
    with open('data.json', 'r') as file:
        return json.load(file)

# Load the template.html file
def load_template():
    with open('template.html', 'r') as file:
        return file.read()

# Load the version from version.txt file
def load_version():
    with open('version.txt', 'r') as file:
        return file.read().strip()

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

# Generate table rows for all funds
def generate_table_rows(funds):
    rows = ""
    for fund in funds:
        scheme_name = fund['Scheme Name']
        scheme_code = fund['Scheme Code']
        nav = format_nav(fund['NAV'])
        row = f'''
        <tr>
            <td><a href="funds/{scheme_code}.html">{scheme_name}</a></td>
            <td>{nav}</td>
            <td>{format_value(fund.get('1D'))}</td>
            <td>{format_value(fund.get('7D'))}</td>
            <td>{format_value(fund.get('1M'))}</td>
            <td>{format_value(fund.get('3M'))}</td>
            <td>{format_value(fund.get('6M'))}</td>
            <td>{format_value(fund.get('1Y'))}</td>
            <td>{format_value(fund.get('3Y'))}</td>
            <td>{format_value(fund.get('5Y'))}</td>
        </tr>
        '''
        rows += row
    return rows

# Replace the placeholders in the template with generated content
def build_index_html(template, table_rows, nav_date, version):
    content = template.replace('{{TABLE_ROWS}}', table_rows)
    content = content.replace('{{NAV_DATE}}', nav_date)
    content = content.replace('{{VERSION}}', version)
    return content

# Save the final index.html file
def save_index_html(content):
    with open('index.html', 'w') as file:
        file.write(content)
    print("index.html has been generated successfully.")

# Main function to orchestrate the build process
def build_site():
    funds = load_base_data()
    template = load_template()
    version = load_version()
    
    # Convert the date of the first fund entry to dd-mm-yyyy format
    nav_date = convert_date_format(funds[0]['Date']) if funds else "N/A"
    
    table_rows = generate_table_rows(funds)
    final_html = build_index_html(template, table_rows, nav_date, version)
    save_index_html(final_html)

# Execute the build process
if __name__ == "__main__":
    build_site()
