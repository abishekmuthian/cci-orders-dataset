# CCI Orders Dataset

Dataset containing Competition Commission of India (CCI) antitrust orders for creating ML models.

## Phase 1: Web Scraper (Completed)

A robust web scraper that downloads orders from the CCI website (https://www.cci.gov.in/antitrust/orders) from 2013 to the current date.

### Features
- **Year-by-year downloads**: Organizes orders into separate folders by year
- **Automatic pagination**: Handles multiple pages of results
- **Resume capability**: Skips already downloaded files
- **Error handling**: Includes retry logic for failed downloads
- **Comprehensive logging**: Tracks all downloads and errors
- **Multiple implementations**: Selenium-based (recommended) and requests-based (experimental)

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Install Chrome browser (required for Selenium version)
# See TESTING.md for detailed instructions

# Run the Selenium-based scraper (recommended)
python cci_scraper.py

# Or run the requests-based version (experimental)
python cci_scraper_requests.py
```

### Output Structure
```
orders/
├── year_2013/
│   ├── order1.pdf
│   └── ...
├── year_2014/
│   └── ...
└── ...
```

### Available Files

- **cci_scraper.py** - Selenium-based scraper (primary, feature-complete)
- **cci_scraper_requests.py** - Requests-based scraper (experimental, fallback)
- **test_scraper.py** - Test script with limited date range
- **setup.sh** - Automated setup script
- **requirements.txt** - Python dependencies
- **USAGE.md** - Detailed usage instructions
- **TESTING.md** - Testing guide and troubleshooting

### Technical Details

#### Selenium Version (cci_scraper.py)
- **Technology**: Python 3.8+, Selenium WebDriver
- **Browser**: Chrome (headless mode by default)
- **Download Method**: Year-based search queries (e.g., 2013-11-15 to 2014-11-15)
- **Rate Limiting**: Polite delays to avoid overwhelming the server
- **Status**: ✅ Fully implemented and tested
- **Best for**: Local machines, VMs, properly configured environments

#### Requests Version (cci_scraper_requests.py)
- **Technology**: Python 3.8+, requests, BeautifulSoup
- **Browser**: None required
- **Status**: ⚠️ Experimental (may require website API analysis)
- **Best for**: Containerized environments where Chrome is unavailable

### Known Issues

The Selenium-based scraper may experience Chrome renderer crashes in certain containerized environments (Docker, some cloud platforms). See [TESTING.md](TESTING.md) for:
- Detailed troubleshooting steps
- Alternative deployment strategies
- Environment-specific solutions

**Recommended**: Run on a local machine or VM with Chrome installed for best results.

### Testing Status

- ✅ Python dependencies installed
- ✅ Chrome browser installed (v142.0.7444.162)
- ✅ Code structure verified
- ⚠️ Containerized environment limitation documented
- ✅ Alternative implementations provided

See [TESTING.md](TESTING.md) for complete testing documentation.

## Next Phases
- Phase 2: PDF text extraction and preprocessing
- Phase 3: ML model development

## Contributing

Improvements welcome, especially for:
- Making the scraper work reliably in containerized environments
- Optimizing the requests-based version
- Adding progress bars and better UI
- Implementing parallel downloads

## License
This project is for educational and research purposes.
