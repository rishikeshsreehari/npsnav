import requests
import json
from datetime import datetime

# Define the headers to mimic a browser visit
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Referer': 'https://www.nseindia.com/'
}

# Create a session to manage cookies
session = requests.Session()
session.headers.update(headers)

# Visit the NSE website to get the necessary cookies
session.get('https://www.nseindia.com/')

# API endpoint to get all indices data
api_url = 'https://www.nseindia.com/api/allIndices'

# Fetch the data from the API
response = session.get(api_url)
data = response.json()

# Initialize the closing price variable
closing_price = None

# Iterate through the data to find Nifty 50
for index in data['data']:
    if index['index'] == 'NIFTY 50':
        closing_price = index['last']
        break

# Check if closing price was found
if closing_price is not None:
    # Format the closing price to two decimal places
    closing_price_formatted = "{:.2f}".format(float(closing_price))
    
    # Get today's date in 'YYYY-MM-DD' format
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Load existing JSON data
    json_file_path = 'data/nifty.json'
    try:
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty dictionary
        json_data = {}
    
    # Check if today's date is already in the data
    if today in json_data:
        # Compare the stored data with the latest data
        if json_data[today] != closing_price_formatted:
            # Update the data with the latest closing price
            json_data[today] = closing_price_formatted
            
            # Save the updated data back to the JSON file
            with open(json_file_path, 'w') as f:
                json.dump(json_data, f, indent=4)
            
            print(f"Updated Nifty price for {today}: {closing_price_formatted}")
        else:
            print(f"Data for {today} is already up to date in '{json_file_path}'.")
    else:
        # Add the new data to the dictionary
        json_data[today] = closing_price_formatted
        
        # Save the updated data back to the JSON file
        with open(json_file_path, 'w') as f:
            json.dump(json_data, f, indent=4)
        
        print(f"Added Nifty price for {today}: {closing_price_formatted}")
else:
    print("Nifty 50 index data not found.")
