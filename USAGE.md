# CCI Orders Scraper - Usage Guide

## Overview
This scraper downloads antitrust orders from the Competition Commission of India (CCI) website.

## Features
- Downloads orders from 2013 to current date
- Year-by-year organization (creates separate folders for each year)
- Handles pagination automatically
- Resume capability (skips already downloaded files)
- Comprehensive logging
- Retry logic for failed downloads
- Headless browser support

## Prerequisites

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Chrome and ChromeDriver

#### Ubuntu/Debian:
```bash
# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f

# ChromeDriver will be managed automatically by webdriver-manager
```

#### macOS:
```bash
brew install --cask google-chrome
# ChromeDriver will be managed automatically by webdriver-manager
```

#### Windows:
Download and install Chrome from https://www.google.com/chrome/
ChromeDriver will be managed automatically by webdriver-manager

## Usage

### Basic Usage
Run the scraper with default settings (downloads from 2013 to current date):
```bash
python cci_scraper.py
```

### Advanced Usage
You can modify the script to customize:
- Start year (default: 2013)
- Headless mode (default: True)
- Download directory (default: ./orders)

Example modifications in the script:
```python
# Change start year
scraper.run(start_year=2015)

# Run with visible browser (for debugging)
scraper = CCIScraper(headless=False)
```

## Output Structure
```
cci-orders-dataset/
├── orders/
│   ├── year_2013/
│   │   ├── order1.pdf
│   │   ├── order2.pdf
│   │   └── ...
│   ├── year_2014/
│   │   └── ...
│   └── ...
└── cci_scraper.log
```

## Logging
The scraper creates a log file `cci_scraper.log` with detailed information about:
- Download progress
- Errors and retries
- Successfully downloaded files
- Skipped files (already exist)

## Resume Capability
If the scraper is interrupted, simply run it again. It will:
- Skip already downloaded PDFs
- Continue from where it left off

## Troubleshooting

### ChromeDriver Issues
If you encounter ChromeDriver errors:
```bash
pip install --upgrade webdriver-manager
```

### Permission Errors
Ensure the script has write permissions for the output directory:
```bash
chmod +w orders/
```

### Website Changes
If the scraper stops working, the website structure may have changed. Check the log file for errors and inspect the website HTML.

### Connection Timeouts
If you experience connection timeouts:
- Check your internet connection
- The scraper has built-in retry logic (3 attempts per download)
- Increase timeout values in the script if needed

## Performance Notes
- The scraper includes polite delays between requests to avoid overwhelming the server
- Full scrape from 2013 may take several hours depending on the number of orders
- Monitor the log file for progress updates

## Rate Limiting
The scraper is designed to be polite:
- 1 second delay between PDF downloads
- 2 seconds delay between years
- 3-5 seconds delay for page navigation

## Support
For issues or questions:
1. Check the log file for error details
2. Ensure all dependencies are installed
3. Verify Chrome and ChromeDriver are properly installed
4. Check if the website structure has changed
