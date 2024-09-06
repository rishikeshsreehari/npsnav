
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

You can use the free API to get the latest NAV for any NPS fund. Access the latest NAV data using the following URL format:
  ```
  https://npsnav.in/api/{scheme_code}
  ```
Replace \`{scheme_code}\` with the scheme code of the fund you are interested in. The API will return the NAV value as plain text. A list of all scheme codes can be found [here](https://npsnav.in/nps-funds-list).

Read more about the [API here](https://npsnav.in/nps-api).

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

## Contributing

Contributions are welcome! Please fork the repository and create a pull request to contribute.

## License

This project is open-source and licensed under the **AGPL-3.0 License**. See the [LICENSE](LICENSE) file for more details.
