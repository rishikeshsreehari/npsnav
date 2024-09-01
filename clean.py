# Script written for cleaning historic value and sort it

import os
import json
from collections import OrderedDict
from datetime import datetime

# Define the directory containing the JSON files
data_folder = "data"

# Function to clean up and sort the JSON data by date
def clean_and_sort_json(data):
    cleaned_data = OrderedDict()

    for key, value in data.items():
        # Clean the date key and value by stripping spaces and quotes
        clean_key = key.strip().replace('"', '')
        clean_value = value.strip().replace('"', '')

        # Check if the cleaned key is in the correct date format
        try:
            parsed_date = datetime.strptime(clean_key, "%m/%d/%Y")
            cleaned_data[clean_key] = clean_value
        except ValueError:
            print(f"Skipping invalid date format: {clean_key}")

    # Sort the dictionary by date in descending order
    sorted_data = OrderedDict(
        sorted(cleaned_data.items(), key=lambda x: datetime.strptime(x[0], "%m/%d/%Y"), reverse=True)
    )
    
    return sorted_data

# Iterate over each file in the data folder
for file_name in os.listdir(data_folder):
    if file_name.endswith('.json'):
        file_path = os.path.join(data_folder, file_name)
        
        # Load the JSON data
        with open(file_path, 'r') as f:
            data = json.load(f, object_pairs_hook=OrderedDict)
        
        # Clean up and sort the data by date
        sorted_data = clean_and_sort_json(data)
        
        # Save the cleaned and sorted data back to the file
        with open(file_path, 'w') as f:
            json.dump(sorted_data, f, indent=4)
        
        print(f"Cleaned and sorted {file_name} by date.")
