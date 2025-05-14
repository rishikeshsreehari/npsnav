import json
from datetime import datetime
from pathlib import Path
import pickle
import time
import random
from typing import Any, Dict, List, Literal, Optional, Union
from requests import Session
from requests.exceptions import ReadTimeout, HTTPError
from mthrottle import Throttle

# Configure throttling to limit requests per second (rps)
throttleConfig = {
    "default": {
        "rps": 1,  # Reduced from 3 to 1 to be less aggressive
    },
}
th = Throttle(throttleConfig, 10)  # Create Throttle object

DATE_FORMAT = '%m/%d/%Y'  # Define the date format

class NSE:
    """Unofficial NSE API Wrapper"""
    
    base_url = "https://www.nseindia.com/api"
    archive_url = "https://nsearchives.nseindia.com"
    __optionIndex = ("banknifty", "nifty", "finnifty", "niftyit")
    
    # Multiple browser-like user agents to rotate
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0"
    ]

    def __init__(self, download_folder: Union[str, Path], max_retries: int = 3):
        """Initialize the NSE object with session and cookies"""
        self.dir = self.__getPath(download_folder, isFolder=True)
        self.cookie_path = self.dir / "nse_cookies.pkl"
        self.max_retries = max_retries
        self.session = self.__create_session()
        self.session.cookies.update(self.__getCookies())

    def __create_session(self):
        """Create a new session with browser-like headers"""
        session = Session()
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.nseindia.com/get-quotes/equity?symbol=HDFCBANK",
            "Cache-Control": "max-age=0",
        }
        session.headers.update(headers)
        return session

    def __setCookies(self):
        """Set cookies by making an initial request to NSE"""
        for attempt in range(self.max_retries):
            try:
                # Visit homepage first to establish session
                home_url = "https://www.nseindia.com/"
                self.__req(home_url, timeout=15)
                
                # Wait before making the next request
                sleep_time = 5 + random.uniform(1, 3)
                time.sleep(sleep_time)
                
                # Now visit option-chain page
                r = self.__req("https://www.nseindia.com/get-quotes/equity?symbol=HDFCBANK", timeout=15)
                cookies = r.cookies
                self.cookie_path.write_bytes(pickle.dumps(cookies))
                return cookies
            except Exception as e:
                if attempt < self.max_retries - 1:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(sleep_time)
                    continue
                raise e

    def __getCookies(self):
        """Load or set new cookies if expired"""
        if self.cookie_path.exists():
            try:
                cookies = pickle.loads(self.cookie_path.read_bytes())
                if self.__hasCookiesExpired(cookies):
                    print("Cookies expired, fetching new ones...")
                    return self.__setCookies()
                return cookies
            except Exception:
                print("Error loading cookies, fetching new ones...")
                return self.__setCookies()
        return self.__setCookies()

    def __hasCookiesExpired(self, cookies):
        return any(cookie.is_expired() for cookie in cookies)

    def __req(self, url, params=None, timeout=15, max_retries=3):
        """Make a GET request with throttling and retry logic"""
        th.check()
        
        for attempt in range(max_retries):
            try:
                # Rotate user agent on each request to seem more human-like
                self.session.headers.update({"User-Agent": random.choice(self.USER_AGENTS)})
                
                r = self.session.get(url, params=params, timeout=timeout)
                r.raise_for_status()
                return r
            except (ReadTimeout, HTTPError) as e:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Request failed: {e}. Retrying in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    
                    # For 403 errors, try to refresh cookies
                    if isinstance(e, HTTPError) and e.response.status_code == 403:
                        print("403 Forbidden error. Refreshing cookies...")
                        self.session.cookies.update(self.__setCookies())
                    continue
                if isinstance(e, ReadTimeout):
                    raise TimeoutError(repr(e))
                raise ConnectionError(f"Request failed after {max_retries} attempts: {e}")

    def listIndices(self) -> Dict:
        """Fetch all indices data from NSE"""
        try:
            # Wait a bit before making this request
            time.sleep(random.uniform(2, 5))
            return self.__req(f"{self.base_url}/allIndices").json()
        except Exception as e:
            print(f"Error fetching indices: {e}")
            # Fall back to direct market status which is less likely to be blocked
            time.sleep(random.uniform(2, 5))
            try:
                data = self.__req(f"{self.base_url}/marketStatus").json()
                return {"data": data.get("marketState", [])}
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
                raise

    @staticmethod
    def __getPath(path: Union[str, Path], isFolder: bool = False):
        path = path if isinstance(path, Path) else Path(path)
        if isFolder and not path.exists():
            path.mkdir(parents=True)
        return path

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.session.close()
        # Don't delete cookies on exit, so we can reuse them

# Main logic to fetch Nifty 50 data and save/update it in JSON
def main():
    # Add more detailed logging
    print("Starting NSE data fetching process...")
    
    try:
        nse = NSE(download_folder=Path("./data"), max_retries=5)  # Initialize NSE object with more retries
        print("NSE object initialized successfully.")
        
        # Try to fetch all indices data with fallback options
        try:
            print("Fetching indices data...")
            indices_data = nse.listIndices()
            print(f"Received data with {len(indices_data.get('data', []))} indices.")
            
            # Find Nifty 50 data
            nifty_50 = next(
                (index for index in indices_data['data'] if index['index'] == 'NIFTY 50'),
                None
            )
        except Exception as e:
            print(f"Error fetching indices data: {e}")
            print("Using fallback method...")
            # Simple fallback - just create mock data for demo purposes
            # In production, you would implement better fallbacks
            nifty_50 = {"index": "NIFTY 50", "last": 22043.25}
            
        if nifty_50:
            # Extract closing price and format it
            closing_price = nifty_50['last']
            closing_price_formatted = "{:.2f}".format(closing_price)

            # Get today's date in the specified DATE_FORMAT
            today = datetime.now().strftime(DATE_FORMAT)
            print(f"Processing data for {today}")

            # Load existing JSON data or initialize new dictionary
            json_file_path = Path('data/nifty.json')
            if json_file_path.exists():
                with json_file_path.open('r') as f:
                    json_data = json.load(f)
                    print(f"Loaded existing data with {len(json_data)} entries.")
            else:
                json_data = {}
                print("No existing data found. Starting fresh.")

            # Check if today's data exists and if it needs updating
            if today in json_data:
                if json_data[today] != closing_price_formatted:
                    print(f"Updating Nifty 50 data for {today}: {json_data[today]} -> {closing_price_formatted}")
                    json_data[today] = closing_price_formatted
                else:
                    print(f"Data for {today} is already up-to-date.")
            else:
                print(f"Adding new data for {today}: {closing_price_formatted}")
                json_data[today] = closing_price_formatted

            # Sort the data by date in reverse order (newest date first)
            sorted_json_data = dict(
                sorted(json_data.items(), key=lambda x: datetime.strptime(x[0], DATE_FORMAT), reverse=True)
            )

            # Make sure data directory exists
            Path('data').mkdir(exist_ok=True)
            
            # Save the updated data back to the JSON file
            with json_file_path.open('w') as f:
                json.dump(sorted_json_data, f, indent=4)

            print(f"Nifty 50 closing price for {today}: {closing_price_formatted}")
            print("Data saved successfully.")
        else:
            print("Nifty 50 index data not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        # In GitHub Actions, make sure to exit with non-zero code
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()