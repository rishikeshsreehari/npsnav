import os
import json

# Load the base data.json file
def load_base_data():
    with open('data.json', 'r') as file:
        return json.load(file)

# Function to generate plain text HTML files for each fund (without any HTML tags)
def generate_api_text_files(funds):
    api_folder = 'api'
    
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

# Main function to orchestrate the API text file generation
def create_api_files():
    funds = load_base_data()
    generate_api_text_files(funds)
    print("All API text files have been generated successfully.")

# Execute the script
if __name__ == "__main__":
    create_api_files()
