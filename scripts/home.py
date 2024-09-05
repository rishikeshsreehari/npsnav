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
    with open('data/data.json', 'r') as file:
        return json.load(file)

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

# Render all HTML files in the content directory
def render_html_files(env, funds):
    table_rows = generate_table_rows(funds)
    nav_date = convert_date_format(funds[0]['Date']) if funds else "N/A"

    for root, dirs, files in os.walk('src/content'):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, 'src/content')
                output_path = os.path.join('public', relative_path)

                # Ensure the output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Load and render the template
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check if the file contains Jinja templating
                if '{%' in content or '{{' in content:
                    template = env.from_string(content)
                    rendered_content = template.render(TABLE_ROWS=table_rows, NAV_DATE=nav_date)
                else:
                    rendered_content = content

                # Save the rendered file
                with open(output_path, 'w') as output_file:
                    output_file.write(rendered_content)
                print(f'Rendered {output_path}')

# Function to create robots.txt and sitemap.xml
def create_robots_and_sitemap(disallowed_paths=None, sitemap_included_paths=None):
    if disallowed_paths is None:
        disallowed_paths = []

    if sitemap_included_paths is None:
        sitemap_included_paths = []

    # robots.txt content
    robots_content = "User-agent: *\n"
    for path in disallowed_paths:
        robots_content += f"Disallow: /{path}\n"
    robots_content += "Disallow:\n"  # Allow all other paths

    # Sitemap XML content
    sitemap_content = "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"

    # Generate sitemap entries
    for root, dirs, files in os.walk('public'):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                url_path = os.path.relpath(file_path, 'public').replace(os.sep, '/')
                
                # Check if the exact path is to be included in the sitemap
                if url_path in sitemap_included_paths:
                    sitemap_content += f"  <url><loc>https://npsnav.in/{url_path}</loc></url>\n"

    sitemap_content += "</urlset>"

    # Write robots.txt
    with open('public/robots.txt', 'w') as robots_file:
        robots_file.write(robots_content)

    # Write sitemap.xml
    with open('public/sitemap.xml', 'w') as sitemap_file:
        sitemap_file.write(sitemap_content)

    print("robots.txt and sitemap.xml have been created.")

# Copy assets to public directory
def copy_assets():
    if os.path.exists('assets'):
        shutil.copytree('assets', 'public/assets', dirs_exist_ok=True)
        print("Assets have been copied.")

# Main function to orchestrate the build process
def build_site():
    env = init_jinja_env()
    funds = load_base_data()
    
    render_html_files(env, funds)
    
    # Customize the paths for robots.txt and sitemap.xml
    disallowed = [
        "api/",        
    ]

    sitemap_included = [
        "index.html",
        "nps-api.html",
        # Add other specific paths here if needed""
    ]
    
    create_robots_and_sitemap(disallowed_paths=disallowed, sitemap_included_paths=sitemap_included)
    copy_assets()

# Execute the build process
if __name__ == "__main__":
    build_site()
