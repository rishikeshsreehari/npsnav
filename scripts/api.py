import os
import json
from datetime import datetime

# Load the base data.json file
def load_base_data():
    with open('data/data.json', 'r') as file:
        return json.load(file)

# Function to format the date in dd/mm/yyyy format
def format_date(date_string):
    try:
        # Assuming the date is provided in the original format as mm/dd/yyyy
        parsed_date = datetime.strptime(date_string, "%m/%d/%Y")
        # Return the date in dd/mm/yyyy format
        return parsed_date.strftime("%d/%m/%Y")
    except ValueError:
        # In case of an invalid date, just return the original string (for safety)
        return date_string

# Function to generate plain text HTML files for each fund (without any HTML tags)
def generate_api_text_files(funds):
    api_folder = 'public/api'
    
    # Create the API directory if it doesn't exist
    if not os.path.exists(api_folder):
        os.makedirs(api_folder)
    
    # Loop through each fund and create a file with just the NAV value
    for fund in funds:
        scheme_code = fund['Scheme Code']
        nav_value = fund['NAV']
        
        # Write the NAV value directly to a file named after the scheme code
        file_path = os.path.join(api_folder, f"{scheme_code}.html")
        with open(file_path, 'w') as file:
            file.write(nav_value)
        
        print(f"Generated {file_path} with NAV: {nav_value}")

# Function to generate detailed JSON files for each fund
def generate_detailed_api_files(funds):
    api_detailed_folder = 'public/api/detailed'
    
    # Create the API/detailed directory if it doesn't exist
    if not os.path.exists(api_detailed_folder):
        os.makedirs(api_detailed_folder)
    
    # Loop through each fund and create a JSON file named after the scheme code
    for fund in funds:
        scheme_code = fund['Scheme Code']
        
        # Rename "Date" key to "Last Updated" and format the date to dd/mm/yyyy
        fund['Last Updated'] = format_date(fund.pop('Date'))
        
        # Write the full fund information to a JSON file
        file_path = os.path.join(api_detailed_folder, f"{scheme_code}.json")
        with open(file_path, 'w') as file:
            json.dump(fund, file, indent=4)
        
        print(f"Generated {file_path}")

# Main function to orchestrate both API text and detailed JSON file generation
def create_api_files():
    funds = load_base_data()
    
    # Generate plain text HTML files with NAV only
    generate_api_text_files(funds)
    
    # Generate detailed JSON files
    generate_detailed_api_files(funds)
    
    print("All API files (text and JSON) have been generated successfully.")

# Execute the script
if __name__ == "__main__":
    create_api_files()
