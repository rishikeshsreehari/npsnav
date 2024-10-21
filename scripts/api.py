import os
import json
from datetime import datetime

# Load the base data.json file
def load_base_data():
    with open('data/data.json', 'r') as file:
        return json.load(file)

# Function to format the date, defaulting to dd-mm-yyyy
def format_date(date_string, output_format="%d-%m-%Y"):
    try:
        parsed_date = datetime.strptime(date_string, "%m/%d/%Y")
        return parsed_date.strftime(output_format)
    except ValueError:
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
        
        # Rename "Date" key to "Last Updated" and format the date to dd-mm-yyyy
        fund['Last Updated'] = format_date(fund.pop('Date'), "%d-%m-%Y")
        
        # Write the full fund information to a JSON file
        file_path = os.path.join(api_detailed_folder, f"{scheme_code}.json")
        with open(file_path, 'w') as file:
            json.dump(fund, file, indent=4)
        
        print(f"Generated {file_path}")

# Function to generate historical JSON files for each fund     
def generate_historical_api_files():
    data_folder = 'data'
    api_historical_folder = 'public/api/historical'
    
    # Create the API/historical directory if it doesn't exist
    if not os.path.exists(api_historical_folder):
        os.makedirs(api_historical_folder)
    
    # Loop through each file in the data folder, ignoring 'data.json'
    for filename in os.listdir(data_folder):
        if filename.endswith('.json') and filename not in ('data.json', 'nifty.json'):  # Skip 'data and nifty json'
            scheme_code = filename.replace('.json', '')
            file_path = os.path.join(data_folder, filename)
            
            # Load the historical data from the file
            with open(file_path, 'r') as file:
                historical_data = json.load(file)
            
            # Prepare the historical data in the new format (with correct date formatting as dd-mm-yyyy)
            historical_list = [
                {
                    "date": format_date(date, "%d-%m-%Y"),
                    "nav": float(nav_value)
                }
                for date, nav_value in historical_data.items()
            ]
            
            # Find the latest date (the max date in the keys)
            latest_date = max(historical_data.keys(), key=lambda d: datetime.strptime(d, "%m/%d/%Y"))
            
            # Construct the full JSON structure
            output_data = {
                "data": historical_list,
                "metadata": {
                    "currency": "INR",
                    "dataType": "NAV",
                    "lastUpdated": format_date(latest_date, "%d-%m-%Y")  # Format as dd-mm-yyyy
                }
            }
            
            # Write the data to the corresponding JSON file in the historical folder
            output_file_path = os.path.join(api_historical_folder, f"{scheme_code}.json")
            with open(output_file_path, 'w') as output_file:
                json.dump(output_data, output_file, indent=4)
            
            print(f"Generated {output_file_path} with last updated date: {format_date(latest_date, '%d-%m-%Y')}")

# Main function to orchestrate both API text and detailed JSON file generation
def create_api_files():
    funds = load_base_data()
    
    # Generate plain text HTML files with NAV only
    generate_api_text_files(funds)
    
    # Generate detailed JSON files
    generate_detailed_api_files(funds)
    
    # Generate historical json files
    generate_historical_api_files()
    
    print("All API files (text and JSON) have been generated successfully.")

# Execute the script
if __name__ == "__main__":
    create_api_files()
