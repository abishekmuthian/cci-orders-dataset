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

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python cci_scraper.py
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

For detailed usage instructions, see [USAGE.md](USAGE.md).

### Technical Details
- **Technology**: Python 3.8+, Selenium WebDriver
- **Browser**: Chrome (headless mode by default)
- **Download Method**: Year-based search queries (e.g., 2013-11-15 to 2014-11-15)
- **Rate Limiting**: Polite delays to avoid overwhelming the server

## Next Phases
- Phase 2: PDF text extraction and preprocessing
- Phase 3: ML model development

## License
This project is for educational and research purposes.
