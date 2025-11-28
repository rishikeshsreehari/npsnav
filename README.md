# NPSNAV.in

**NPSNAV.in** is a website that tracks the **Latest NAV and Historical Performance of NPS Funds** in India.  
It provides up-to-date insights into the National Pension Scheme (NPS) fund performances, including:

- Latest Net Asset Value (NAV)
- Historical NAV trends
- Detailed fund performance metrics
- Easy-to-use APIs for Google Sheets, Excel, and other financial tools

---

## Features

- Displays all NPS funds with their latest NAV, performance data, and fund manager (PFM) details.
- Provides historical NAV data for every NPS fund.
- Data is fetched directly from **Protean eGov Technologies Limited** (formerly NSDL e-Governance Infrastructure Limited).
- Each fund has its own dedicated page with detailed performance data.
- Includes a **FREE, zero-auth API** with multiple formats:
  - Simple (plain text)
  - Detailed (JSON)
  - Latest all-funds dump (JSON)
  - Historical NAV (JSON)
  - Minimal lightweight API (JSON)
- Fully static website — HTML, CSS, and JS are minified for performance.
- Updated twice daily using GitHub Actions + Cloudflare Pages.

---

## API Usage

Easily integrate real-time and historical NAV data for any NPS fund using our API.  
**Five types of APIs** are available:

---

### 1. Simple API (Plain Text)

Fetch the latest NAV using a scheme code:

```
https://npsnav.in/api/{scheme_code}
```

Example:

```
https://npsnav.in/api/SM001001
```

Returns:

```
46.7686
```

---

### 2. Detailed API (JSON)

Returns full fund details (NAV + returns).

```
https://npsnav.in/api/detailed/{scheme_code}
```

Example Response:

```json
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

---

### 3. Latest API (All Funds, Detailed JSON)

Fetch the latest NAV and metadata **for all NPS funds at once**:

```
https://npsnav.in/api/latest
```

Example Response:

```json
{
  "data": [
    {
      "PFM Code": "PFM001",
      "PFM Name": "SBI PENSION FUNDS PRIVATE LIMITED",
      "Scheme Code": "SM001001",
      "Scheme Name": "SBI PENSION FUND SCHEME - CENTRAL GOVT",
      "NAV": "46.7686",
      "Last Updated": "01-10-2024"
    }
  ],
  "metadata": {
    "currency": "INR",
    "dataType": "NAV",
    "count": 151,
    "lastUpdated": "01-10-2024"
  }
}
```

---

### 4. Latest-Min API (All Funds, Minimal JSON)

Lightweight version containing only Scheme Code and NAV.

```
https://npsnav.in/api/latest-min
```

Response:

```json
{
  "data": [
    ["SM001001", 46.7686],
    ["SM008001", 93.4021]
  ],
  "metadata": {
    "currency": "INR",
    "dataType": "NAV",
    "count": 151,
    "lastUpdated": "01-10-2024"
  }
}
```

---

### 5. Historical API (JSON)

Retrieve historical NAVs:

```
https://npsnav.in/api/historical/{scheme_code}
```

Example Response:

```json
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

---

### Scheme Code List
A full list of scheme names and codes:  
👉 https://npsnav.in/nps-funds-list

### Full API Documentation  
👉 https://npsnav.in/nps-api

---

## Makefile Commands

The project includes a convenient `Makefile` that simplifies common development tasks.

```makefile
.PHONY: install build serve clean dev deploy update

# Install dependencies
install:
	uv sync

# Build the static site
build:
	uv run scripts/build.py

# Build the site quickly without full build
quick:
	uv run scripts/main.py

# Serve the site locally
serve:
	uv run scripts/serve_local.py

# Clean build artifacts
clean:
	rm -rf public

# Default development flow: build and serve
dev: build serve

# Deploy to Cloudflare
deploy:
	npx wrangler pages deploy public

# Update content: fetch new data, build, and deploy
update:
	uv run scripts/fetch.py
	$(MAKE) build
	$(MAKE) deploy
```

### What Each Command Does

| Command | Description |
|--------|-------------|
| `make install` | Installs dependencies using **uv**. |
| `make build` | Builds the full static site using `scripts/build.py`. |
| `make quick` | Fast rebuild using only `scripts/main.py`. |
| `make serve` | Starts a local server for development. |
| `make clean` | Removes generated files. |
| `make dev` | Builds the site and starts the dev server. |
| `make deploy` | Deploys the site to Cloudflare Pages. |
| `make update` | Fetches data, builds the site, and deploys it. |

---

## Setup Instructions

### Prerequisites
- Python 3.x installed
- `pip` installed for dependency management

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/rishikeshsreehari/npsnav.in.git
   cd npsnav.in
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Project

1. **Fetch Data**
   ```bash
   python3 scripts/fetch.py
   ```

2. **Build the Static Site**
   ```bash
   python3 scripts/build.py
   ```

3. **View Output**
   ```bash
   cd public
   python3 -m http.server
   ```

---

## Automation with GitHub Actions

- NAV data is fetched **twice daily at 11 AM and 11 PM IST**.
- GitHub Actions runs `fetch.py` and commits changes automatically.
- Cloudflare Pages rebuilds and deploys the latest data.

---

## Hosting & Analytics

- Hosted on **Cloudflare Pages** for global low-latency.  
- Analytics powered by **GoatCounter**:  
  https://npsnav.goatcounter.com/

(API usage is not tracked.)

---

## Contributing

Contributions and pull requests are welcome!  
Issues and feature suggestions:  
👉 https://github.com/rishikeshsreehari/npsnav/issues

---

## License

This project uses a **dual-license model**:

### **1. Code License**
- Licensed under **AGPL-3.0**
- Applies to all source code  
- See the [LICENSE](LICENSE) file

### **2. Data License**
- Dataset files under `/data` are licensed under  
  **Creative Commons Attribution–NonCommercial 4.0 (CC BY-NC 4.0)**  
- Personal, educational, and non-commercial use is allowed  
- Commercial use is prohibited without written permission  

See the [DATA_LICENSE](DATA_LICENSE) file for details.
