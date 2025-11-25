
# NPSNAV.in

**NPSNAV.in** is a website that tracks the **Latest NAV and Historical Performance of NPS Funds** in India. It provides up-to-date insights into the National Pension Scheme (NPS) fund performances, including the latest Net Asset Value (NAV) and historical returns, with an easy-to-use API for Google Sheets, Microsoft Excel, and other financial planning tools.

## Features

- Displays all NPS funds with their latest NAV and performance data.
- Provides historical returns for each fund over different timeframes.
- Data is fetched directly from Protean eGov Technologies Limited (formerly NSDL e-Governance Infrastructure Limited).
- Each fund has its own dedicated page with detailed performance data.
- A **FREE API** provides easy access to the latest NPS fund NAVs, with the API returning the latest NAV as plain text.
- The project's HTML, CSS, and JavaScript are minified for optimized performance.

## API Usage

Easily integrate real-time and historical NAV data for any NPS fund with our API. Three types of APIs are currently available:

### Simple API
Fetch the latest NAV of any NPS fund using its scheme code.
  ```
  https://npsnav.in/api/{scheme_code}
  ```
The API will return the NAV value as plain text.

### Detailed API

Get detailed information about an NPS fund, including returns over various timeframes.

```
https://npsnav.in/api/detailed/{scheme_code}
```
Sample Result:

```
{
  "Last Updated": "01-10-2024",
  "PFM Code": "PFM001",
  "PFM Name": "SBI PENSION FUNDS PRIVATE LIMITED",
  "Scheme Code": "SM001001",
  "Scheme Name": "SBI PENSION FUND SCHEME - CENTRAL GOVT",
  "NAV": "46.7686",
  "1D": "0.10",
  "7D": "0.13",
  "1M": "1.34",
  "3M": "3.51",
  "6M": "6.73",
  "1Y": "13.98",
  "3Y": "8.16",
  "5Y": "9.23"
}
```

### Historical API

Retrieve historical NAV data for any NPS fund.

```
https://npsnav.in/api/historical/{scheme_code}
```
Sample Result:

```
 {
  "data": [
    {
      "date": "01-10-2024",
      "nav": 46.7686
    },
    {
      "date": "30-09-2024",
      "nav": 46.7231
    }
  ],
  "metadata": {
    "currency": "INR",
    "dataType": "NAV",
    "lastUpdated": "01-10-2024"
  }
}
```
Replace `{scheme_code}` with the scheme code of the fund you are interested in. A list of all scheme codes can be found [here](https://npsnav.in/nps-funds-list).

Read more about [APIs here](https://npsnav.in/nps-api).

## Setup Instructions

To run the project locally, follow the steps below:

### Prerequisites
- Python 3.x
- `pip` to install required Python packages.

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/rishikeshsreehari/npsnav.in.git
   cd npsnav.in
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Project

1. **Fetch Data**: Run the following command to fetch the latest NAV data:
   ```
   python3 scripts/fetch.py
   ```

2. **Build the Site**: After fetching the data, build the static site by running:
   ```
   python3 scripts/build.py
   ```

3. **View Output**: The generated files will be available in the `public` directory. You can open the `index.html` file in a browser to view the site or start a local server by running `python3 -m http.server` inside the public directory.

### Automation with GitHub Actions

GitHub Actions trigger `fetch.py` every day at **11 AM** and **11 PM IST**. This script fetches the latest NAV data and commits any changes, which automatically triggers a build on Cloudflare to keep the site updated. Check `daily-fetch.yml` for more details.

## Hosting and Stats

The site is hosted on Cloudflare Pages. The stats are collected using GoatCounter and can be viewed [here](https://npsnav.goatcounter.com/). Please note that these stats do not include API calls.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request to contribute.

Some existing bugs and enhancements can be viewed in the [issues section](https://github.com/rishikeshsreehari/npsnav/issues).

## License

This project uses a dual-license model:

- **Code** is open-source and licensed under the **AGPL-3.0 License**.  
  See the [LICENSE](LICENSE) file for details.

- **Dataset** (files in the `/data` directory) is licensed under the  
  **Creative Commons Attribution–NonCommercial 4.0 License (CC BY-NC 4.0)**.  
  See the [DATA_LICENSE](DATA_LICENSE) file for usage terms.

Personal, educational, and non-commercial use of the dataset is permitted.  
Commercial use is prohibited without prior written permission.