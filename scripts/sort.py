import os
import json
from collections import OrderedDict
from datetime import datetime

# Configurable variables
data_folder_path = 'data'  # Path to the folder containing JSON files
ascending_order = False    # Set to True for ascending, False for descending order

# Function to sort JSON data by date
def sort_json_by_date(file_path, ascending=True):
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Sort the dictionary by date, converting the date strings to datetime objects
    sorted_data = OrderedDict(
        sorted(data.items(), key=lambda x: datetime.strptime(x[0], '%m/%d/%Y'), reverse=not ascending)
    )

    # Write the sorted data back to the file
    with open(file_path, 'w') as file:
        json.dump(sorted_data, file, indent=4)

# Function to loop through all JSON files in the 'data' folder
def sort_all_jsons_in_folder(folder_path, ascending=True):
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            print(f"Sorting file: {file_path}")
            sort_json_by_date(file_path, ascending)

# Sort all JSON files in the folder
sort_all_jsons_in_folder(data_folder_path, ascending=ascending_order)
