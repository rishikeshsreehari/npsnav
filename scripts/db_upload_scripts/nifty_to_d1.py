import json
import os
import subprocess

# Configuration
data_file = 'data/nifty.json'  # Path to nifty.json
output_folder = 'output_sql_files_nifty'  # Folder to save SQL files
database_name = 'npsnav'  # Replace with your actual D1 database name
batch_size = 100  # Number of rows per SQL file for splitting

# Step 1: Load JSON data
def load_nifty_data():
    with open(data_file, 'r') as file:
        data = json.load(file)
    return data

# Step 2: Create SQL file with INSERT statements
def create_sql_file(nifty_data):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    sql_file_path = os.path.join(output_folder, 'nifty_daily_values.sql')
    with open(sql_file_path, 'w') as sql_file:
        for date, nav in nifty_data.items():
            sql_file.write(
                f"INSERT INTO nifty_daily_values (date, nav) VALUES ('{date}', {nav}) "
                f"ON CONFLICT (date) DO UPDATE SET nav = excluded.nav;\n"
            )
    return sql_file_path

# Step 3: Split SQL file into smaller batches if needed
def split_sql_file(sql_file_path, batch_size):
    with open(sql_file_path, 'r') as file:
        lines = file.readlines()

    # Split lines into batches
    for i in range(0, len(lines), batch_size):
        batch_lines = lines[i:i + batch_size]
        batch_filename = f"nifty_batch_{i // batch_size + 1}.sql"
        batch_file_path = os.path.join(output_folder, batch_filename)
        with open(batch_file_path, 'w') as batch_file:
            batch_file.writelines(batch_lines)

# Step 4: Upload SQL files to Cloudflare D1
def upload_file(file_path):
    """Attempt to upload a single file to Cloudflare D1."""
    print(f"Uploading {file_path} to Cloudflare D1...")
    process = subprocess.run(
        ["npx", "wrangler", "d1", "execute", database_name, "--remote", "--file", file_path],
        capture_output=True,
        text=True,
        encoding='utf-8',
        shell=True
    )
    if process.returncode == 0:
        print(f"Successfully uploaded {os.path.basename(file_path)}")
        return True
    else:
        print(f"Failed to upload {os.path.basename(file_path)}: {process.stderr}")
        return False

def upload_all_batches():
    uploaded_files = []
    failed_files = []

    for filename in sorted(os.listdir(output_folder)):
        if filename.startswith("nifty_batch") and filename.endswith(".sql"):
            file_path = os.path.join(output_folder, filename)
            if upload_file(file_path):
                uploaded_files.append(filename)
            else:
                failed_files.append(filename)

    # Log summary
    print("\n--- Upload Summary ---")
    print("Successfully uploaded files:")
    for file in uploaded_files:
        print(f" - {file}")

    if failed_files:
        print("\nFailed to upload files:")
        for file in failed_files:
            print(f" - {file}")
    else:
        print("All files uploaded successfully.")

if __name__ == "__main__":
    # Load JSON data
    nifty_data = load_nifty_data()

    # Create SQL file with INSERT statements
    sql_file_path = create_sql_file(nifty_data)

    # Split SQL file into batches
    split_sql_file(sql_file_path, batch_size)

    # Upload all SQL batches to Cloudflare D1
    upload_all_batches()
