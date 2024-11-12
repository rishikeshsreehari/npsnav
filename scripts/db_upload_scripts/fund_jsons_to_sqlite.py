import os
import json
import sqlite3
from datetime import datetime

# Define constants
DATE_FORMAT = '%m/%d/%Y'
DB_PATH = "fund_data.db"  # Path to your SQLite database file

def create_database():
    """Set up a new SQLite database and create the required table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fund_daily_values (
            fund_id TEXT,
            date TEXT,
            nav REAL,
            PRIMARY KEY (fund_id, date)
        )
    ''')
    conn.commit()
    conn.close()
    print("Database created and table set up.")

def insert_data(cursor, fund_id, data):
    """Insert JSON data into the SQLite database."""
    for date_str, nav in data.items():
        # Convert the date format to YYYY-MM-DD for compatibility
        date_obj = datetime.strptime(date_str, DATE_FORMAT).strftime('%Y-%m-%d')
        cursor.execute(
            "INSERT OR REPLACE INTO fund_daily_values (fund_id, date, nav) VALUES (?, ?, ?)",
            (fund_id, date_obj, float(nav))
        )

def process_json_files(data_folder):
    """Process each JSON file and insert data into the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for filename in os.listdir(data_folder):
        if filename.endswith('.json') and filename not in {'data.json', 'nifty.json'}: #exclude these files
            fund_id = filename.replace('.json', '')  # Use the filename (without .json) as fund_id
            file_path = os.path.join(data_folder, filename)
            
            # Load JSON data from file
            with open(file_path, 'r') as file:
                data = json.load(file)
                insert_data(cursor, fund_id, data)
                print(f"Inserted data for {fund_id}")
    
    conn.commit()
    conn.close()
    print(f"Data from JSON files has been loaded into {DB_PATH}.")

if __name__ == "__main__":
    # Directory containing your JSON files
    data_folder = "./data"
    
    # Step 1: Create the database and table
    create_database()
    
    # Step 2: Process JSON files and insert data into the database
    process_json_files(data_folder)
    
    print("All data has been processed and stored in the SQLite database.")
