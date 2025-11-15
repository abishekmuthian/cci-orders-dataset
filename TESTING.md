# Testing and Deployment Guide

## Environment Compatibility

### Known Issues in Containerized Environments

The Selenium-based scraper (`cci_scraper.py`) may experience Chrome renderer crashes in certain containerized environments (Docker, some cloud platforms) due to:
- Missing system libraries
- Seccomp/AppArmor restrictions
- Insufficient shared memory
- Display/GPU limitations

### Testing Results

#### Environment Tested
- **Platform**: Linux 4.4.0 (Ubuntu 24.04)
- **Python**: 3.11.14
- **Chrome**: 142.0.7444.162
- **Issue**: Chrome tab crashes when attempting to load pages in containerized environment

```
selenium.common.exceptions.WebDriverException: Message: tab crashed
```

## Recommended Deployment Approaches

### Option 1: Local Machine (Recommended)

The scraper works best on a local machine with a GUI environment or properly configured headless setup.

**Steps:**
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Chrome browser (if not already installed)
4. Run the scraper:
   ```bash
   python cci_scraper.py
   ```

### Option 2: Virtual Machine / EC2 Instance

Deploy on a virtual machine with full system access:

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip
sudo apt-get install -y wget gnupg

# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f

# Clone and run
git clone <repository-url>
cd cci-orders-dataset
pip3 install -r requirements.txt
python3 cci_scraper.py
```

### Option 3: Docker with Proper Configuration

If you must use Docker, use a specialized Selenium container:

```dockerfile
FROM selenium/standalone-chrome:latest

USER root
RUN apt-get update && apt-get install -y python3 python3-pip
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY cci_scraper.py .
USER seluser

CMD ["python3", "cci_scraper.py"]
```

### Option 4: Manual Download with Browser

If automated scraping is not possible, the website can be accessed manually:
1. Visit https://www.cci.gov.in/antitrust/orders#tab-2a
2. Enter date range (e.g., 2024-01-01 to 2024-12-31)
3. Click search
4. Download PDFs from each page

## Alternative Scraper Versions

### Selenium-based (cci_scraper.py)
- **Pros**: Handles JavaScript, pagination, dynamic content
- **Cons**: Requires Chrome/ChromeDriver, may fail in containers
- **Best for**: Local machines, VMs, properly configured environments

### Requests-based (cci_scraper_requests.py)
- **Pros**: No browser required, works in constrained environments
- **Cons**: May not work if website uses JavaScript for content loading
- **Best for**: Simple websites, API endpoints
- **Status**: Experimental - may need API endpoint analysis

## Troubleshooting

### Chrome Crashes
If you see "tab crashed" errors:
1. Check Chrome version: `google-chrome --version`
2. Verify shared memory: `df -h /dev/shm`
3. Try non-headless mode (set `headless=False` in script)
4. Check system resources: `free -h`
5. Try single-process mode (add `--single-process` to Chrome options, not recommended for production)

### Missing ChromeDriver
```bash
pip install --upgrade webdriver-manager
```

### Permission Errors
```bash
chmod +x cci_scraper.py
mkdir -p orders
chmod 755 orders
```

### Website Changes
If the scraper stops working:
1. Check if website structure has changed
2. Inspect browser network tab to see actual requests
3. Update selectors in the code
4. Check logs for specific errors

## Performance Optimization

### For Large-Scale Scraping
- Use pagination efficiently
- Implement rate limiting (already included)
- Consider parallel downloads (modify script)
- Monitor disk space for PDFs

### Memory Management
- Run one year at a time for very large datasets
- Clear browser cache periodically
- Monitor memory usage: `watch -n 1 free -h`

## Validation

After scraping, validate the downloads:
```bash
# Count total PDFs
find orders -name "*.pdf" | wc -l

# Check for empty files
find orders -name "*.pdf" -size 0

# List files by year
for year in orders/year_*; do
    echo "$year: $(ls $year | wc -l) files"
done
```

## Support and Issues

If you encounter issues:
1. Check the log files (`cci_scraper.log`, `test_scraper.log`)
2. Verify your environment meets requirements
3. Try the test script: `python test_scraper.py`
4. Consider using a non-containerized environment

## Next Steps

Once scraping is successful:
1. Verify downloaded PDFs are valid
2. Extract text from PDFs (Phase 2)
3. Preprocess data for ML models (Phase 3)
