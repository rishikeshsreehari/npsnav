import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import json

# Convert date from mm/dd/yyyy to dd-mm-yyyy format
def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%d-%m-%Y")
    except ValueError:
        return date_str

# Load the base data.json file to get NAV_DATE
def load_base_data():
    with open('data/data.json', 'r') as file:
        return json.load(file)

# Function to create robots.txt and sitemap.xml
def create_robots_and_sitemap(funds, disallowed_paths=None):
    if disallowed_paths is None:
        disallowed_paths = []

    # robots.txt content
    robots_content = "User-agent: *\n"
    for path in disallowed_paths:
        robots_content += f"Disallow: /{path}\n"
    robots_content += "Disallow:\n"  # Allow all other paths

    # Get the NAV_DATE for lastmod
    nav_date = convert_date_format(funds[0]['Date']) if funds else "N/A"

    # Sitemap XML content
    sitemap_content = "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"

    # Generate sitemap entries
    for root, dirs, files in os.walk('public'):
        for file in files:
            # Avoiding api folder and html files inside api folder
            if file.endswith('.html') and 'api' not in root and '404.html' not in file:
            
                file_path = os.path.join(root, file)
                url_path = os.path.relpath(file_path, 'public').replace(os.sep, '/')

                # Special case for index.html (should point to the root URL)
                if url_path.endswith('index.html'):
                    url_path = url_path[:-10]  # Remove '/index.html' to represent the root or subfolder

                # Remove the ".html" extension for other pages
                elif url_path.endswith('.html'):
                    url_path = url_path[:-5]  # Remove the '.html' extension

                sitemap_content += f"  <url><loc>https://npsnav.in/{url_path}</loc><lastmod>{nav_date}</lastmod></url>\n"

    sitemap_content += "</urlset>"

    # Write robots.txt
    with open('public/robots.txt', 'w') as robots_file:
        robots_file.write(robots_content)

    # Write sitemap.xml
    with open('public/sitemap.xml', 'w') as sitemap_file:
        sitemap_file.write(sitemap_content)

    print("robots.txt and sitemap.xml have been created.")

# Main function to generate robots.txt and sitemap.xml
def build_robots_and_sitemap():
    funds = load_base_data()
    
    # Customize the paths for robots.txt and sitemap.xml
    disallowed = [
        "api/",        
    ]
    
    create_robots_and_sitemap(funds, disallowed_paths=disallowed)

# Execute the robots.txt and sitemap.xml generation
if __name__ == "__main__":
    build_robots_and_sitemap()
