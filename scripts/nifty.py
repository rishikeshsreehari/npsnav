import json
from datetime import datetime
from pathlib import Path
import pickle
from typing import Any, Dict, List, Literal, Optional, Union
from requests import Session
from requests.exceptions import ReadTimeout
from mthrottle import Throttle

# Configure throttling to limit requests per second (rps)
throttleConfig = {
    "default": {
        "rps": 3,  # Requests per second
    },
}
th = Throttle(throttleConfig, 10)  # Create Throttle object

DATE_FORMAT = '%m/%d/%Y'  # Define the date format

class NSE:
    """Unofficial NSE API Wrapper"""
    
    base_url = "https://www.nseindia.com/api"
    archive_url = "https://nsearchives.nseindia.com"
    __optionIndex = ("banknifty", "nifty", "finnifty", "niftyit")

    def __init__(self, download_folder: Union[str, Path]):
        """Initialize the NSE object with session and cookies"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/118.0",
            "Accept": "*/*",
            "Referer": "https://www.nseindia.com/get-quotes/equity?symbol=HDFCBANK",
        }
        self.dir = self.__getPath(download_folder, isFolder=True)
        self.cookie_path = self.dir / "nse_cookies.pkl"
        self.session = Session()
        self.session.headers.update(headers)
        self.session.cookies.update(self.__getCookies())

    def __setCookies(self):
        """Set cookies by making an initial request to NSE"""
        r = self.__req("https://www.nseindia.com/option-chain", timeout=10)
        cookies = r.cookies
        self.cookie_path.write_bytes(pickle.dumps(cookies))
        return cookies

    def __getCookies(self):
        """Load or set new cookies if expired"""
        if self.cookie_path.exists():
            cookies = pickle.loads(self.cookie_path.read_bytes())
            if self.__hasCookiesExpired(cookies):
                return self.__setCookies()
            return cookies
        return self.__setCookies()

    def __hasCookiesExpired(self, cookies):
        return any(cookie.is_expired() for cookie in cookies)

    def __req(self, url, params=None, timeout=10):
        """Make a GET request with throttling"""
        th.check()
        try:
            r = self.session.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r
        except ReadTimeout as e:
            raise TimeoutError(repr(e))
        except Exception as e:
            raise ConnectionError(f"Request failed: {e}")

    def listIndices(self) -> Dict:
        """Fetch all indices data from NSE"""
        return self.__req(f"{self.base_url}/allIndices").json()

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
        self.cookie_path.unlink(missing_ok=True)

# Main logic to fetch Nifty 50 data and save/update it in JSON
def main():
    nse = NSE(download_folder=Path("./data"))  # Initialize NSE object

    try:
        # Fetch all indices data
        indices_data = nse.listIndices()
        
        # Find Nifty 50 data
        nifty_50 = next(
            (index for index in indices_data['data'] if index['index'] == 'NIFTY 50'),
            None
        )

        if nifty_50:
            # Extract closing price and format it
            closing_price = nifty_50['last']
            closing_price_formatted = "{:.2f}".format(closing_price)

            # Get today's date in the specified DATE_FORMAT
            today = datetime.now().strftime(DATE_FORMAT)

            # Load existing JSON data or initialize new dictionary
            json_file_path = Path('data/nifty.json')
            if json_file_path.exists():
                with json_file_path.open('r') as f:
                    json_data = json.load(f)
            else:
                json_data = {}

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

            # Save the updated data back to the JSON file
            with json_file_path.open('w') as f:
                json.dump(sorted_json_data, f, indent=4)

            print(f"Nifty 50 closing price for {today}: {closing_price_formatted}")
        else:
            print("Nifty 50 index data not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
