"""
Seed missing NPS funds into data/data.json so they can be backfilled.

- Reads: data/missing_funds.json
- Appends seed rows to: data/data.json
- Safe to run multiple times (idempotent)
"""

import json
import os
from datetime import datetime

DATA_FILE = "data/data.json"
MISSING_FILE = "data/missing_funds.json"
SEED_DATE = "01/01/1900"
SEED_NAV = "0"


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def main():
    if not os.path.exists(MISSING_FILE):
        print(f"❌ Missing file: {MISSING_FILE}")
        return

    missing_report = load_json(MISSING_FILE, {})
    new_funds = missing_report.get("new_combinations", [])

    if not new_funds:
        print("✓ No missing funds to seed")
        return

    data = load_json(DATA_FILE, [])
    existing_keys = {
        (row["PFM Code"], row["Scheme Code"])
        for row in data
        if "PFM Code" in row and "Scheme Code" in row
    }

    added = 0

    for fund in new_funds:
        key = (fund["PFM Code"], fund["Scheme Code"])
        if key in existing_keys:
            continue

        seed_row = {
            "Date": SEED_DATE,
            "PFM Code": fund["PFM Code"],
            "PFM Name": fund["PFM Name"],
            "Scheme Code": fund["Scheme Code"],
            "Scheme Name": fund["Scheme Name"],
            "NAV": SEED_NAV,
        }

        data.append(seed_row)
        existing_keys.add(key)
        added += 1

        print(f"➕ Seeded {fund['PFM Code']}/{fund['Scheme Code']}")

    if added == 0:
        print("✓ All missing funds already seeded")
        return

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print(f"\n✓ Added {added} seed entries to {DATA_FILE}")
    print("✓ Next step: run fetch_nav.py to backfill real NAV data")


if __name__ == "__main__":
    main()
