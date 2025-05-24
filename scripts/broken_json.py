import os
import json

def find_broken_json():
    data_folder = 'data'
    
    for filename in os.listdir(data_folder):
        if filename.endswith('.json') and filename not in ('data.json', 'nifty.json'):
            file_path = os.path.join(data_folder, filename)
            try:
                with open(file_path, 'r') as file:
                    json.load(file)
                print(f"✓ {filename} - Valid JSON")
            except json.JSONDecodeError as e:
                print(f"✗ {filename} - BROKEN: {e}")
                # Show the problematic line
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                    if len(lines) >= 7:
                        print(f"Line 7: {lines[6].strip()}")

if __name__ == "__main__":
    find_broken_json()