import json

# Load existing data
with open('data/data.json', 'r') as f:
    existing = json.load(f)

# Load missing funds
with open('data/missing_funds.json', 'r') as f:
    missing = json.load(f)

# Add placeholder entries for new funds (will be updated by fetch_nav.py)
for fund in missing['new_combinations']:
    existing.append({
        "Date": "01/01/2024",  # Placeholder, will be replaced
        "PFM Code": fund['PFM Code'],
        "PFM Name": fund['PFM Name'],
        "Scheme Code": fund['Scheme Code'],
        "Scheme Name": fund['Scheme Name'],
        "NAV": "0"  # Placeholder
    })

# Save back
with open('data/data.json', 'w') as f:
    json.dump(existing, f, indent=4)

print(f"Added {len(missing['new_combinations'])} new funds to data.json")