import requests
import json
from datetime import datetime
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Base URL
WORKER_BASE_URL = 'https://npsnav.rishikeshsreehari.workers.dev'

# Create a session
session = requests.Session()
session.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.1.2222.33 Safari/537.36",
    "Accept-Encoding": "*",
    "Connection": "keep-alive",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def test_endpoints():
    print("Testing endpoints...")
    
    # Test fund endpoint
    try:
        print("Making request to latest-fund endpoint...")
        fund_response = session.get(
            f"{WORKER_BASE_URL}/latest-fund",
            params={'fund_id': 'SM001001'},
            verify=False,  # Disable SSL verification for testing
            timeout=10  # Set timeout in seconds
        )
        print("Fund Response Status:", fund_response.status_code)
        print("Fund Response:", fund_response.text)
        
        if fund_response.ok:
            fund_data = fund_response.json()
            print("Latest Fund Date:", fund_data.get('date'))
    except requests.Timeout:
        print("Fund request timed out.")
    except Exception as e:
        print("Fund Error:", str(e))

    # Test Nifty endpoint
    try:
        print("Making request to latest-nifty endpoint...")
        nifty_response = session.get(
            f"{WORKER_BASE_URL}/latest-nifty",
            verify=False,  # Disable SSL verification for testing
            timeout=10  # Set timeout in seconds
        )
        print("Nifty Response Status:", nifty_response.status_code)
        print("Nifty Response:", nifty_response.text)
        
        if nifty_response.ok:
            nifty_data = nifty_response.json()
            print("Latest Nifty Date:", nifty_data.get('date'))
    except requests.Timeout:
        print("Nifty request timed out.")
    except Exception as e:
        print("Nifty Error:", str(e))

if __name__ == "__main__":
    test_endpoints()
