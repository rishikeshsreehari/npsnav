import os
import subprocess

# Configuration
output_folder = 'output_sql_files'  # Folder containing the split SQL files
database_name = 'npsnav'  # Replace with your actual D1 database name

# List of fund_id values to ignore
ignore_fund_ids = [
    'SM006001', 'SM006002', 'SM006003', 'SM006004', 'SM006005', 'SM006006', 'SM006007', 'SM006008', 'SM006009',
    'SM009001', 'SM009002', 'SM009003', 'SM009004', 'SM009005', 'SM009006', 'SM009007'
]

def filter_and_upsert_lines(file_path, ignore_fund_ids):
    """Filter out lines with specific fund_id values and add ON CONFLICT for upserts."""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    modified_lines = []
    for line in lines:
        # Skip lines containing any fund_id in ignore_fund_ids
        if any(f"'{fund_id}'" in line or f'"{fund_id}"' in line for fund_id in ignore_fund_ids):
            continue
        # Modify insert statements to use ON CONFLICT for upsert
        if line.strip().startswith("INSERT INTO fund_daily_values"):
            line = line.replace(
                ");",
                ") ON CONFLICT (fund_id, date) DO UPDATE SET nav = excluded.nav;"
            )
        modified_lines.append(line)

    # Rewrite the file with filtered and modified lines
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(modified_lines)

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

if __name__ == "__main__":
    # Process all files in the output folder
    uploaded_files = []
    still_failed_files = []

    for filename in os.listdir(output_folder):
        if filename.endswith(".sql"):
            file_path = os.path.join(output_folder, filename)
            
            # Filter and add upsert logic to each file
            filter_and_upsert_lines(file_path, ignore_fund_ids)
            
            # Attempt to upload the modified file
            if upload_file(file_path):
                uploaded_files.append(filename)
            else:
                still_failed_files.append(filename)

    # Log summary
    print("\n--- Upload Summary ---")
    print("Successfully uploaded files:")
    for file in uploaded_files:
        print(f" - {file}")

    print("\nStill failed to upload files:")
    for file in still_failed_files:
        print(f" - {file}")
