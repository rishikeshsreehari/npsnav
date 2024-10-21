from datetime import datetime
import json
from pathlib import Path

# Main logic to fetch Nifty 50 data, convert date format, and save/update it in JSON
def main():
    # Define the path to the JSON file
    json_file_path = Path('data/nifty.json')

    try:
        # Load the existing JSON data
        if json_file_path.exists():
            with json_file_path.open('r') as f:
                json_data = json.load(f)
        else:
            print(f"File {json_file_path} does not exist.")
            return

        # Check the current format of the dates and convert if necessary
        new_json_data = {}
        for old_date, price in json_data.items():
            try:
                # Check if the date is already in 'MM/DD/YYYY' format
                datetime.strptime(old_date, '%m/%d/%Y')
                # If it's already in the correct format, just copy it to the new dictionary
                new_json_data[old_date] = price
            except ValueError:
                # If the date is in 'YYYY-MM-DD' format, convert it to 'MM/DD/YYYY'
                old_date_obj = datetime.strptime(old_date, '%Y-%m-%d')
                new_date_format = old_date_obj.strftime('%m/%d/%Y')
                new_json_data[new_date_format] = price

        # Sort the dictionary by date in reverse order (newest first)
        sorted_json_data = dict(
            sorted(new_json_data.items(), key=lambda x: datetime.strptime(x[0], '%m/%d/%Y'), reverse=True)
        )

        # Save the updated data back to the JSON file in the new format
        with json_file_path.open('w') as f:
            json.dump(sorted_json_data, f, indent=4)

        print("Dates successfully converted to MM/DD/YYYY format with newest at the top.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
