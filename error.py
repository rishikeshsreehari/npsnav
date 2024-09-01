import os
import json
from collections import OrderedDict
from datetime import datetime

# Define the directory containing the JSON files
data_folder = "data"

# Function to sort the JSON data by date in descending order
def sort_json_by_date(data):
    sorted_data = OrderedDict()

    for key, value in sorted(data.items(), key=lambda x: datetime.strptime(x[0].strip().replace('"', ''), "%m/%d/%Y"), reverse=True):
        sorted_data[key] = value

    return sorted_data

# Iterate over each file in the data folder
for file_name in os.listdir(data_folder):
    if file_name.endswith('.json'):
        file_path = os.path.join(data_folder, file_name)
        
        # Load the JSON data
        with open(file_path, 'r') as f:
            data = json.load(f, object_pairs_hook=OrderedDict)
        
        # Sort the data by date
        sorted_data = sort_json_by_date(data)
        
        # Save the sorted data back to the file
        with open(file_path, 'w') as f:
            json.dump(sorted_data, f, indent=4)
        
        print(f"Sorted {file_name} by date.")
