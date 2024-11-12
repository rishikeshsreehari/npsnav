import json
import subprocess
import pandas as pd

# Load data from your JSON file
with open("data/data.json", "r") as f:
    data = json.load(f)

# Create a list to hold the processed data
processed_data = []

# Process the data
for record in data:
    fund_id = record["Scheme Code"]
    fund_name = record["Scheme Name"]
    fund_manager = record["PFM Name"]
    
    # Derive `tier` and `scheme` from the name (accounting for uppercase "TIER")
    tier = "I" if "TIER I" in fund_name else "II" if "TIER II" in fund_name else None
    scheme = "E" if "SCHEME E" in fund_name else "C" if "SCHEME C" in fund_name else \
             "G" if "SCHEME G" in fund_name else "A" if "SCHEME A" in fund_name else "OTHERS"
    
    # Add to processed data list
    processed_data.append({
        "fund_id": fund_id,
        "fund_name": fund_name,
        "fund_manager": fund_manager,
        "tier": tier,
        "scheme": scheme
    })

# Convert the processed data to a DataFrame
df = pd.DataFrame(processed_data)

# Print each fund's details in the terminal
for index, row in df.iterrows():
    print(f"Fund ID: {row['fund_id']}, Fund Name: {row['fund_name']}, "
          f"Fund Manager: {row['fund_manager']}, Tier: {row['tier']}, Scheme: {row['scheme']}")

# Insert data into D1 using wrangler d1 execute
for index, row in df.iterrows():
    fund_id = row['fund_id']
    fund_name = row['fund_name']
    fund_manager = row['fund_manager']
    tier = row['tier']
    scheme = row['scheme']

    # Construct the SQL command for each row
    sql_command = f"""
    INSERT INTO Funds (fund_id, fund_name, fund_manager, tier, scheme)
    VALUES ('{fund_id}', '{fund_name}', '{fund_manager}', '{tier}', '{scheme}');
    """
    
    # Ensure SQL command is a string and passed properly
    sql_command = sql_command.replace("\n", " ").replace("\r", "")  # Clean up the command
    
    # Execute the command with Wrangler using subprocess
    process = subprocess.run(
        ["wrangler", "d1", "execute", "npsnav","--remote", "--command", sql_command],
        capture_output=True,
        text=True,
        shell=True,
        encoding='utf-8'  # Set encoding to handle any special characters
    )

    if process.returncode == 0:
        print(f"Inserted: {fund_id}")
    else:
        print(f"Failed to insert {fund_id}: {process.stderr}")
