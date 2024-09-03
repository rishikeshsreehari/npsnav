import json
import os


# Load the data.json file
with open('data/data.json', 'r') as f:
    funds_data = json.load(f)

# Check for missing keys in each fund
for fund in funds_data:
    print(f"Fund data: {fund}")
    missing_keys = []
    required_keys = ["1M", "3M", "6M", "1Y", "3Y", "5Y"]
    for key in required_keys:
        if key not in fund:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"Fund '{fund['Scheme Name']}' (Scheme Code: {fund['Scheme Code']}) is missing keys: {', '.join(missing_keys)}")
