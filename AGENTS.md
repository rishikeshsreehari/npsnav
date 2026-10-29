# NPSNAV.in - Architecture & Technical Documentation

## Overview

**NPSNAV.in** is a static website and free API that tracks the latest NAV (Net Asset Value) and historical performance of all NPS (National Pension Scheme) funds in India. The project fetches data from **Protean eGov Technologies Limited** (formerly NSDL), calculates returns, generates static HTML pages and API endpoints, and deploys automatically to Cloudflare Pages.

### Key Features
- 📊 Tracks ~280 NPS funds across 11 PFMs (Pension Fund Managers)
  - Includes Regular (POP), Direct, and Government Subscriber variants
- 🔄 Updates 3x daily (11 AM, 3 PM, 11 PM IST) via GitHub Actions
- 🌐 100% static site - no backend server required
- 🔓 Free, zero-auth API with multiple formats (text, JSON, historical)
- 📈 Calculates returns for 1D, 7D, 1M, 3M, 6M, 1Y, 3Y, 5Y periods
- 🚀 Deployed on Cloudflare Pages for global low-latency access
- ⚡ Multiple NAV Framework support (added April 2026)

---

## Project Structure

```
npsnav/
├── data/                      # NAV data storage
│   ├── data.json             # Latest NAV for all funds (with returns)
│   ├── changelog.json        # Version history
│   ├── nifty.json           # Nifty 50 index data
│   ├── missing_funds.json   # New funds discovered (pending manual review)
│   ├── SM001001.json        # Individual fund historical data (280+ files)
│   ├── SM001022.json        # New GS variant schemes (since April 1, 2026)
│   ├── SM001025.json        # New DIRECT variant schemes (since April 1, 2026)
│   └── ...
├── src/
│   ├── templates/           # Jinja2 HTML templates
│   └── content/             # Static HTML content
├── scripts/                 # Python automation scripts
│   ├── fetch.py            # Fetch NAV data from NPS Trust
│   ├── build.py            # Orchestrates the full build process
│   ├── calculate.py        # Calculate returns (1D, 7D, 1M, etc.)
│   ├── main.py             # Generate HTML pages from templates
│   ├── api.py              # Generate API endpoints (JSON/text)
│   ├── funds.py            # Generate individual fund pages
│   ├── minify.py           # Minify HTML/CSS/JS
│   ├── robots-sitemap.py   # Generate sitemap and robots.txt
│   ├── discover_new_funds.py  # Monthly fund discovery
│   └── nifty.py            # Fetch Nifty 50 data
├── public/                  # Generated static site (gitignored)
│   ├── index.html
│   ├── api/                # API endpoints
│   │   ├── {scheme_code}.html     # Plain text NAV
│   │   ├── detailed/{scheme_code}.json
│   │   ├── historical/{scheme_code}.json
│   │   ├── latest.json
│   │   ├── latest-min.json
│   │   └── schemes.json
│   └── funds/              # Individual fund pages
│       └── {scheme_code}.html
├── .github/workflows/
│   ├── daily-fetch.yml     # Runs fetch.py twice daily
│   └── fund-discovery.yml  # Monthly new fund discovery
├── Makefile                # Build automation
├── requirements.txt
└── README.md
```

---

## Data Flow Architecture

### 1. Data Fetching (`fetch.py`)

**Runs**: Twice daily (11 AM & 11 PM IST) via GitHub Actions

**Process**:
1. Reads existing `data/data.json` to get PFM-scheme mappings
2. Downloads Excel/TSV files from NPS Trust for each scheme
3. Parses NAV data (handles multiple formats: TSV, CSV, Excel)
4. **Only saves NEW records** (prevents duplicates via date checking)
5. Updates individual scheme files (`SM001001.json`, etc.)
6. Updates `data/data.json` with latest NAVs
7. Commits changes to git

**Key Features**:
- Concurrent downloads (3 workers) for performance
- Multiple parser fallbacks (TSV → CSV → xlrd → openpyxl → calamine)
- Backfill support (adds missing historical dates)
- Retry logic with exponential backoff
- Date deduplication per scheme

**Data Source**: 
```
https://npstrust.org.in/scheme-wise-nav-report-excel
?navcatdataxls={PFM_CODE}&navyearselxls=12&navsubdataxls={SCHEME_CODE}
```

---

### 2. Return Calculation (`calculate.py`)

**Runs**: After fetch.py, before build

**Process**:
1. Reads `data/data.json` and individual scheme files
2. For each fund, calculates returns by comparing current NAV with historical NAVs:
   - **1D, 7D, 1M, 3M, 6M, 1Y**: Simple returns `((current - past) / past) * 100`
   - **3Y, 5Y**: Annualized (CAGR) returns
3. Implements **staleness detection**: 
   - If fund data is too old (e.g., 10 days), short-term returns are set to `null`
   - Prevents misleading returns for outdated data
4. Updates `data/data.json` with calculated returns

**Smart Date Matching**:
- Uses "strictly previous available date" (e.g., for 1M, finds closest date ≤ 30 days ago)
- Handles weekends, holidays, and missing data gracefully

---

### 3. Site Building (`build.py`)

**Runs**: Before deployment

**Orchestrates** the following scripts in sequence:
1. `calculate.py` - Calculate returns
2. `main.py` - Generate HTML pages
3. `api.py` - Generate API endpoints
4. `funds.py` - Generate individual fund pages
5. `minify.py` - Minify HTML/CSS/JS
6. `robots-sitemap.py` - Generate SEO files

---

### 4. HTML Page Generation (`main.py`)

**Generates**:
- `index.html` - Main table with all funds
- `changelog.html` - Version history
- `nps-funds-list.html` - Scheme code list
- Static content pages (API docs, Excel/Sheets guides)

**Features**:
- Jinja2 templating
- Normalizes PFM names (e.g., "SBI Pension Funds Pvt. Ltd." → "SBI Pension Funds")
- Extracts tier (Tier I / Tier II)
- Classifies scheme types (Scheme A/C/E/G, MSF, Corporate, Vatsalya)
- Generates filterable table rows with data attributes
- Custom scheme type ordering

**Fund Classification Logic**:
```python
MSF_SCHEMES = {"SM001019", "SM001020", ...}  # Model Selection Funds

def extract_scheme_type(scheme_name, scheme_code):
    if scheme_code in MSF_SCHEMES:
        return "MSF"
    if "CORPORATE" in name:
        return "Corporate"
    if "VATSALYA" in name:
        return "Vatsalya"
    if "SCHEME A" in name:
        return "Scheme A"
    # ... etc
```

---

### 5. API Generation (`api.py`)

**Generates 6 API types**:

#### 1. Simple API (Plain Text)
```
GET /api/{scheme_code}.html
Returns: "49.7499"
```

#### 2. Detailed API (JSON)
```json
GET /api/detailed/{scheme_code}.json
{
  "Last Updated": "04-02-2026",
  "PFM Code": "PFM001",
  "PFM Name": "SBI Pension Funds",
  "Scheme Code": "SM001001",
  "NAV": "49.7499",
  "1D": "0.22", "7D": "0.48", "1M": "1.15",
  "3M": "2.87", "6M": "6.45", "1Y": "12.34",
  "3Y": "8.21", "5Y": "9.45"
}
```

#### 3. Latest API (All Funds)
```json
GET /api/latest.json
{
  "data": [/* all 170+ funds */],
  "metadata": {
    "currency": "INR",
    "dataType": "NAV",
    "count": 170,
    "lastUpdated": "04-02-2026"
  }
}
```

#### 4. Latest-Min API (Compact)
```json
GET /api/latest-min.json
{
  "data": [
    ["SM001001", 49.7499],
    ["SM001002", 42.6964]
  ],
  "metadata": {...}
}
```

#### 5. Historical API
```json
GET /api/historical/{scheme_code}.json
{
  "data": [
    {"date": "04-02-2026", "nav": 49.7499},
    {"date": "03-02-2026", "nav": 49.642}
  ],
  "metadata": {...}
}
```

#### 6. Schemes API
```json
GET /api/schemes.json
{
  "data": [
    ["SM001001", "SBI PENSION FUND SCHEME - CENTRAL GOVT"],
    ["SM001002", "SBI PENSION FUND SCHEME - STATE GOVT"]
  ],
  "metadata": {...}
}
```

---

### 6. Individual Fund Pages (`funds.py`)

**Generates**: `/funds/{scheme_code}.html` for each fund

**Features**:
- Current NAV and returns table
- Historical NAV chart (Chart.js)
- Fund vs Nifty 50 comparison chart
- Data range (first date to last date)

---

### 7. Minification (`minify.py`)

- Minifies all HTML files in `public/` for faster loading
- Reduces file sizes by ~30-40%

---

### 8. SEO Files (`robots-sitemap.py`)

**Generates**:
- `robots.txt` - Search engine crawling rules
- `sitemap.xml` - All fund pages for SEO indexing

---

## Automation Workflows

### Daily Fetch Workflow (`daily-fetch.yml`)

**Schedule**: 
- 11:00 AM IST (05:30 UTC)
- 11:00 PM IST (17:30 UTC)

**Steps**:
1. Checkout repo
2. Install dependencies
3. Run `fetch.py` (download NAV data)
4. Run `nifty.py` (fetch Nifty 50 data)
5. Run `update_db.py` (push to external DB - optional)
6. Force-add `data/SM*.json` files (normally gitignored)
7. Commit: `"Daily NAV update - 2026-02-05 08:39:36 UTC"`
8. Push to GitHub
9. **Cloudflare Pages auto-deploys** on push to main

---

### Fund Discovery Workflow (`fund-discovery.yml`)

**Schedule**: 5th of every month (10:00 AM IST)

**Steps**:
1. Run `discover_new_funds.py`
2. Checks for new PFM/scheme combinations from NPS Trust
3. If new funds found:
   - Saves to `data/missing_funds.json`
   - Commits and pushes
   - **Creates GitHub issue** with fund list
4. Manual review required to add funds to `data.json`

---

## Build Process

### Quick Build (Development)
```bash
make quick    # Only runs main.py
make serve    # Starts local server
```

### Full Build (Production)
```bash
make build    # Runs build.py (full pipeline)
```

**Full Build Steps** (`build.py`):
```python
subprocess.run(['python', 'scripts/calculate.py'])
subprocess.run(['python', 'scripts/main.py'])
subprocess.run(['python', 'scripts/api.py'])
subprocess.run(['python', 'scripts/funds.py'])
subprocess.run(['python', 'scripts/minify.py'])
subprocess.run(['python', 'scripts/robots-sitemap.py'])
```

---

## Data Schema

### `data/data.json` (Latest NAVs)
```json
[
  {
    "Date": "02/04/2026",           // mm/dd/yyyy format
    "PFM Code": "PFM001",
    "PFM Name": "SBI Pension Funds Pvt. Ltd.",
    "Scheme Code": "SM001001",
    "Scheme Name": "SBI PENSION FUND SCHEME - CENTRAL GOVT",
    "NAV": "49.7499",
    "1D": "0.22",  "7D": "0.48",  "1M": "1.15",
    "3M": "2.87",  "6M": "6.45",  "1Y": "12.34",
    "3Y": "8.21",  "5Y": "9.45"
  }
]
```

### `data/SM001001.json` (Historical)
```json
{
  "02/04/2026": "49.7499",
  "02/03/2026": "49.642",
  "02/02/2026": "49.2874",
  ...
}
```
- Sorted by date (newest first)
- Key: `mm/dd/yyyy`, Value: NAV string

### `data/changelog.json`
```json
[
  {
    "version": "v1.4.2",
    "date": "2026-02-05",
    "changes": [
      "Added newly launched NPS Vatsalya funds to the dataset"
    ]
  }
]
```

---

## Key Technical Decisions

### 1. Why Static Site?
- **Performance**: No server-side processing, instant responses
- **Cost**: Free hosting on Cloudflare Pages
- **Reliability**: No backend to crash
- **Scalability**: CDN handles millions of requests
- **SEO**: All pages are pre-rendered HTML

### 2. Why Git-Committed Data?
- **Version control**: Track every NAV change
- **Backup**: Full history in git
- **Transparency**: Public audit trail
- **CI/CD**: Auto-deploy on data changes

### 3. Why Individual Scheme Files?
- Each scheme can have 3000+ historical records
- Single `data.json` would be ~50MB
- Individual files enable:
  - Fast partial updates
  - Efficient API responses
  - Parallel processing

### 4. Date Format: `mm/dd/yyyy`
- Internal format for consistency
- API responses convert to `dd-mm-yyyy` (Indian standard)

---

## Common Operations

### Add a New Fund Manually
1. Add entry to `data/data.json`:
   ```json
   {
     "Date": "02/04/2026",
     "PFM Code": "PFM001",
     "PFM Name": "...",
     "Scheme Code": "SM001XXX",
     "Scheme Name": "...",
     "NAV": "10.0000"
   }
   ```
2. Run `python scripts/fetch.py` to backfill historical data
3. Rebuild: `make build`

### Update Changelog
1. Edit `data/changelog.json` (add to top):
   ```json
   {
     "version": "v1.5.0",
     "date": "2026-04-13",
     "changes": [
       "Added new feature X",
       "Fixed bug Y"
     ]
   }
   ```
2. Update version in templates if needed

### Test Locally
```bash
make install    # Install dependencies
make dev        # Build + serve
# Open http://localhost:8000
```

---

## Dependencies

### Python Packages
```
requests        # HTTP requests to NPS Trust
pandas          # Data parsing (Excel, CSV)
jinja2          # HTML templating
openpyxl        # Excel parsing
xlrd            # Legacy Excel format
calamine        # Fast Excel parsing
beautifulsoup4  # HTML parsing
minify-html     # HTML minification
python-dateutil # Date calculations
```

### External Services
- **Data Source**: NPS Trust (npstrust.org.in)
- **Hosting**: Cloudflare Pages
- **Analytics**: GoatCounter
- **CI/CD**: GitHub Actions

---

## Performance Metrics

- **Site Size**: ~10MB (minified)
- **API Response**: <50ms (via Cloudflare CDN)
- **Build Time**: ~2 minutes (170+ funds)
- **Data Updates**: 2x daily
- **Uptime**: 99.9%+ (Cloudflare SLA)

---

## Licensing

### Code: AGPL-3.0
- All source code
- Requires open-sourcing modifications

### Data: CC BY-NC 4.0
- Dataset files under `/data`
- Personal/educational use allowed
- Commercial use prohibited without permission

---

## Future Tasks & Roadmap

### 🔥 High Priority (Q2 2026)

#### 1. Multiple NAV Framework - UX Improvements
**Status:** Data backfilled ✅, UX pending ⏳

**What:** Add variant filtering to help users choose between Regular/Direct/Government schemes

**Tasks:**
- [ ] Add `extract_variant()` function to `scripts/main.py`
- [ ] Update `generate_table_rows()` to include variant data attribute
- [ ] Add "Variant" filter dropdown in `src/templates/` or `src/content/index.html`
- [ ] Update JavaScript filter to handle variant filtering
- [ ] Add variant badges/indicators in table rows
- [ ] Show NAV difference between Regular vs Direct (e.g., "Direct: +0.07% higher")
- [ ] Update nps-funds-list page to group by variant
- [ ] Add educational content explaining Regular vs Direct vs Government

**Reference:** See `MAIN_PY_UPDATES.md` and `MIGRATION_GUIDE.md`

**User Impact:** High - helps users make informed decisions about lower-fee Direct plans

---

#### 2. Optimize Fetch Schedule Based on NPS Trust Update Time
**Status:** Using conservative 11 AM schedule ⏳

**What:** Determine exact time NPS Trust updates data after PFM aggregation

**Tasks:**
- [ ] Run manual tests at 10:00, 10:15, 10:30, 10:45, 11:00 AM IST
- [ ] Check which time first gets current day's NAV (not previous day)
- [ ] Move morning fetch to optimal time (potentially 10:15-10:30 AM IST)
- [ ] Document findings in AGENTS.md
- [ ] Update workflow comments with actual NPS Trust update time

**Current Schedule:**
- 11:00 AM IST (05:30 UTC)
- 3:00 PM IST (09:30 UTC) - new mid-day fetch
- 11:00 PM IST (17:30 UTC)

**User Impact:** Medium - earlier data availability

---

#### 3. Enhanced Scheme Classification
**Status:** Basic classification working ✅, room for improvement ⏳

**What:** Improve scheme type detection for edge cases

**Tasks:**
- [ ] Review all 280 schemes for correct classification
- [ ] Add new Swasthya schemes to classification logic
- [ ] Handle "POP" suffix schemes (Vatsalya POP, etc.)
- [ ] Add scheme family grouping (group Regular/Direct/GS variants together)
- [ ] Create scheme relationship mapping (show "This scheme also available as: Direct, GS")

**Current Issues:**
- Some new schemes might be classified as "Others"
- Vatsalya POP vs Direct variants need clear distinction
- New Swasthya funds (SM011021, SM013021) need classification

**User Impact:** Medium - better filtering and discovery

---

### 📊 Medium Priority (Q3 2026)

#### 4. API Enhancements

**Tasks:**
- [ ] Add `/api/compare/{code1}/{code2}` endpoint for side-by-side comparison
- [ ] Add `/api/variants/{base_code}` to show all variants of a scheme
- [ ] Add `/api/schemes?variant=direct` filtering
- [ ] Add `/api/schemes?pfm=PFM001` filtering
- [ ] Add `/api/top-performers?period=1Y&limit=10` endpoint
- [ ] Add CORS headers documentation
- [ ] Create API rate limiting documentation
- [ ] Generate TypeScript types from OpenAPI spec
- [ ] Add API changelog/versioning

**User Impact:** High for API users - better programmatic access

---

#### 5. Performance & Monitoring

**Tasks:**
- [ ] Add performance metrics to fetch.py (track download times per PFM)
- [ ] Create monitoring dashboard for GitHub Actions success/failure rates
- [ ] Add alerting for failed fetches (email/Slack/Discord)
- [ ] Track data freshness (alert if data is >24 hours old)
- [ ] Add healthcheck endpoint `/api/health` with last update time
- [ ] Optimize build.py execution time (currently ~2 minutes)
- [ ] Add build time tracking to identify bottlenecks
- [ ] Implement incremental builds (only rebuild changed pages)

**User Impact:** Low for users, high for maintainer

---

#### 6. Data Quality & Validation

**Tasks:**
- [ ] Add NAV validation (detect anomalies like sudden 50% drops)
- [ ] Add data completeness checks (missing dates, gaps in history)
- [ ] Create daily data quality report in GitHub Actions logs
- [ ] Add script to backfill missing historical dates
- [ ] Detect and flag PFM-specific data issues
- [ ] Add automated testing for data integrity
- [ ] Compare NAVs across Regular/Direct/GS variants (should be close)

**User Impact:** High - ensures data accuracy

---

### 🚀 Low Priority / Nice to Have (Q4 2026+)

#### 7. Advanced Features

- [ ] **Portfolio Tracker**: Users can input holdings and track performance
- [ ] **NAV Alerts**: Email/SMS when NAV crosses threshold
- [ ] **Comparison Tool**: Visual charts comparing multiple funds
- [ ] **Performance Rankings**: Top/bottom performers by period
- [ ] **Expense Ratio Calculator**: Show fee impact over time (Regular vs Direct)
- [ ] **Retirement Calculator**: Project corpus based on contributions
- [ ] **Fund Screener**: Filter by returns, risk, PFM, etc.
- [ ] **Historical Returns Heatmap**: Visual calendar of daily returns

#### 8. API Extensions

- [ ] **GraphQL API**: More flexible querying
- [ ] **WebSocket API**: Real-time NAV updates
- [ ] **Bulk API**: Download all data in single request
- [ ] **Webhook Support**: Subscribe to NAV updates
- [ ] **API Key System**: Track usage, rate limiting

#### 9. Integrations

- [ ] **Google Sheets Add-on**: Official add-on for easier integration
- [ ] **Excel Plugin**: Native Excel integration
- [ ] **Telegram Bot**: Query NAVs via Telegram
- [ ] **Discord Bot**: NAV updates in Discord channels
- [ ] **WhatsApp Bot**: NAV queries via WhatsApp
- [ ] **Slack App**: Enterprise NPS tracking
- [ ] **Notion Integration**: Embed NAV data in Notion

#### 10. Mobile & Apps

- [ ] **Progressive Web App (PWA)**: Installable mobile experience
- [ ] **React Native App**: Native iOS/Android app
- [ ] **Widget Support**: iOS/Android home screen widgets
- [ ] **Dark Mode**: System-aware dark theme
- [ ] **Offline Support**: View cached data offline

#### 11. Content & Education

- [ ] **NPS Guide**: Comprehensive guide to NPS investing
- [ ] **PFM Comparison**: Detailed PFM profiles and analysis
- [ ] **Scheme Guides**: Explain Scheme E, C, G, A differences
- [ ] **Tax Calculator**: Calculate tax benefits
- [ ] **Blog**: Market updates, NPS news, analysis
- [ ] **Video Tutorials**: How to use the API
- [ ] **FAQ Section**: Common questions answered

---

## 🐛 Known Issues & Technical Debt

### High Priority
- [ ] Some Vatsalya DIRECT schemes missing from data.json (check missing_funds.json)
- [ ] Verify all 110 new DIRECT/GS schemes have correct PFM names
- [ ] Test build.py with 280 schemes (ensure no memory issues)
- [ ] Update OpenAPI spec to document new scheme variants

### Medium Priority
- [ ] Standardize PFM name normalization (some inconsistencies)
- [ ] Add retry logic for Cloudflare Pages deployments
- [ ] Improve error messages in fetch.py (more descriptive)
- [ ] Add logging levels (DEBUG, INFO, WARNING, ERROR)

### Low Priority
- [ ] Refactor main.py (function too long, split into modules)
- [ ] Add type hints to all Python scripts
- [ ] Add unit tests for calculate.py logic
- [ ] Add integration tests for fetch.py
- [ ] Improve code documentation (docstrings)

---

## 📈 Metrics to Track

### User Metrics
- [ ] API requests per endpoint per day
- [ ] Most requested scheme codes
- [ ] Geographic distribution of users
- [ ] Peak usage times
- [ ] Bounce rate on homepage
- [ ] Time on site / pages per session

### Data Metrics
- [ ] Daily fetch success rate (%)
- [ ] Average fetch duration (seconds)
- [ ] Number of new records per fetch
- [ ] Data freshness (hours since last update)
- [ ] PFM-specific fetch failures
- [ ] NAV anomaly detection count

### System Metrics
- [ ] Build time (seconds)
- [ ] Deploy time (seconds)
- [ ] API response time (ms)
- [ ] CDN cache hit rate (%)
- [ ] GitHub Actions quota usage

---

## 🎯 Success Criteria

### Q2 2026 Goals
- ✅ All 280 schemes (170 original + 110 new) in data.json
- ✅ Historical data backfilled from April 1, 2026
- ⏳ Variant filtering live on homepage
- ⏳ User can compare Regular vs Direct NAVs easily
- ⏳ 3 fetches per day working reliably

### Q3 2026 Goals
- Compare API endpoint live
- API rate limiting documented
- Performance monitoring dashboard
- <1% fetch failure rate

### Q4 2026 Goals
- 100K+ API requests per month
- Portfolio tracker beta launch
- Mobile PWA launch
- Sub-100ms API response time

---

## 💡 Ideas from Community

### From Ranjit (April 10, 2026)
- ✅ Add DIRECT scheme variants (completed)
- ⏳ Earlier fetch times (investigating)
- Suggested: Show fee savings calculator (Regular vs Direct)

### Future Suggestions to Track
- Add scheme inception date to data
- Show fund manager tenure
- Add benchmark comparison (vs Nifty 50)
- Historical volatility metrics
- Sharpe ratio / risk-adjusted returns

---

## 🔧 Development Workflow Improvements

- [ ] Add pre-commit hooks (linting, formatting)
- [ ] Set up automated testing in CI/CD
- [ ] Add staging environment for testing
- [ ] Create CONTRIBUTING.md guide
- [ ] Add issue templates for GitHub
- [ ] Set up Dependabot for dependency updates
- [ ] Add semantic versioning automation
- [ ] Create release notes automation

---

## 📚 Documentation Improvements

- [ ] Add API examples in multiple languages (Python, JavaScript, curl, Excel, Sheets)
- [ ] Create video tutorial for Google Sheets integration
- [ ] Document fetch.py internals (for contributors)
- [ ] Add troubleshooting guide
- [ ] Create architecture diagrams
- [ ] Document data schema in detail
- [ ] Add API migration guide (if breaking changes)

---

## 🌟 Community & Growth

- [ ] Create Discord/Slack community
- [ ] Start Twitter/X account for updates
- [ ] Publish on Product Hunt
- [ ] Submit to Hacker News
- [ ] Add "Sponsor" button on GitHub
- [ ] Create contributor recognition system
- [ ] Host monthly community calls
- [ ] Create ambassador program

---

**Last Updated:** April 13, 2026  
**Next Review:** May 1, 2026

---

## Troubleshooting

### Fetch Failures
- Check NPS Trust website availability
- Verify PFM/scheme codes in `data.json`
- Review error logs in GitHub Actions

### Missing Returns
- Ensure `calculate.py` runs before `main.py`
- Check if historical data file exists for scheme
- Verify date format consistency

### Build Errors
- Clear `public/` directory: `make clean`
- Reinstall dependencies: `make install`
- Check template syntax errors

---

## Contact & Contribution

- **GitHub**: https://github.com/rishikeshsreehari/npsnav
- **Issues**: https://github.com/rishikeshsreehari/npsnav/issues
- **Analytics**: https://npsnav.goatcounter.com/
- **Community**: See README for links

Contributions welcome! Please open an issue before major changes.
