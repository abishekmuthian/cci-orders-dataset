#!/usr/bin/env python3
"""
CCI Orders Scraper
Downloads orders from Competition Commission of India website
URL: https://www.cci.gov.in/antitrust/orders
"""

import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cci_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CCIScraper:
    """Scraper for CCI orders from cci.gov.in"""

    BASE_URL = "https://www.cci.gov.in/antitrust/orders#tab-2a"
    DOWNLOAD_DIR = "orders"

    def __init__(self, headless: bool = True):
        """Initialize the scraper with Chrome driver"""
        self.headless = headless
        self.driver = None
        self.wait = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')

        # Essential options for containerized/headless environments
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-in-process-stack-traces')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-hang-monitor')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-prompt-on-repost')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--force-color-profile=srgb')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--safebrowsing-disable-auto-update')
        chrome_options.add_argument('--enable-automation')
        chrome_options.add_argument('--password-store=basic')
        chrome_options.add_argument('--use-mock-keychain')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        # User agent to avoid detection
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')

        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Set download preferences
        prefs = {
            "download.default_directory": os.path.abspath(self.DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0
        }
        chrome_options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise

    def generate_date_ranges(self, start_year: int = 2013) -> List[Tuple[str, str]]:
        """
        Generate year-by-year date ranges from start_year to current date
        Returns list of tuples (from_date, to_date) in format YYYY-MM-DD
        """
        current_date = datetime.now()
        current_year = current_date.year

        date_ranges = []

        for year in range(start_year, current_year + 1):
            # Start from November 15 for the first year as per user example
            if year == start_year:
                from_date = f"{year}-11-15"
            else:
                from_date = f"{year}-01-01"

            # End date is either Nov 15 next year, Dec 31 same year, or current date
            if year == current_year:
                to_date = current_date.strftime("%Y-%m-%d")
            else:
                to_date = f"{year}-12-31"

            date_ranges.append((from_date, to_date))
            logger.info(f"Generated date range: {from_date} to {to_date}")

        return date_ranges

    def navigate_to_order_tab(self):
        """Navigate to the orders page and click on the order date tab"""
        logger.info(f"Navigating to {self.BASE_URL}")
        self.driver.get(self.BASE_URL)
        time.sleep(3)  # Wait for page to load

        try:
            # Wait for the tab to be clickable
            tab_element = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#tab-2a']"))
            )
            tab_element.click()
            logger.info("Clicked on order date tab")
            time.sleep(2)
        except TimeoutException:
            logger.warning("Order date tab not found or already active")

    def fill_date_form(self, from_date: str, to_date: str):
        """Fill the date form with from and to dates"""
        logger.info(f"Filling date form: {from_date} to {to_date}")

        try:
            # Clear and fill from date
            from_date_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "fromdate"))
            )
            from_date_input.clear()
            from_date_input.send_keys(from_date)

            # Clear and fill to date
            to_date_input = self.driver.find_element(By.ID, "todate")
            to_date_input.clear()
            to_date_input.send_keys(to_date)

            time.sleep(1)

            # Click search button
            search_button = self.driver.find_element(By.ID, "btn-filter-order")
            search_button.click()
            logger.info("Clicked search button")

            # Wait for results to load
            time.sleep(5)

        except Exception as e:
            logger.error(f"Error filling date form: {e}")
            raise

    def get_pdf_links_from_page(self) -> List[Tuple[str, str]]:
        """
        Extract PDF links from the current page
        Returns list of tuples (pdf_url, pdf_name)
        """
        pdf_links = []

        try:
            # Wait for table to be present
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )

            # Find all links in the orders column
            # Look for PDF links in the table
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

            for row in rows:
                try:
                    # Find PDF link in the row
                    pdf_link_element = row.find_element(By.CSS_SELECTOR, "a[href*='.pdf']")
                    pdf_url = pdf_link_element.get_attribute('href')

                    # Extract filename from URL
                    pdf_name = pdf_url.split('/')[-1]
                    if not pdf_name.endswith('.pdf'):
                        pdf_name += '.pdf'

                    pdf_links.append((pdf_url, pdf_name))

                except NoSuchElementException:
                    continue

            logger.info(f"Found {len(pdf_links)} PDF links on current page")

        except Exception as e:
            logger.error(f"Error extracting PDF links: {e}")

        return pdf_links

    def download_pdf(self, pdf_url: str, save_path: str, max_retries: int = 3) -> bool:
        """Download a PDF file with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {pdf_url} (attempt {attempt + 1}/{max_retries})")

                response = requests.get(pdf_url, timeout=30, stream=True)
                response.raise_for_status()

                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logger.info(f"Successfully downloaded: {save_path}")
                return True

            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to download {pdf_url} after {max_retries} attempts")

        return False

    def get_total_pages(self) -> int:
        """Get total number of pages from pagination"""
        try:
            pagination = self.driver.find_element(By.CSS_SELECTOR, "ul.pagination")
            page_items = pagination.find_elements(By.TAG_NAME, "li")

            # Filter out previous/next buttons and get page numbers
            page_numbers = []
            for item in page_items:
                try:
                    text = item.text.strip()
                    if text.isdigit():
                        page_numbers.append(int(text))
                except:
                    continue

            total_pages = max(page_numbers) if page_numbers else 1
            logger.info(f"Total pages found: {total_pages}")
            return total_pages

        except NoSuchElementException:
            logger.info("No pagination found, assuming single page")
            return 1
        except Exception as e:
            logger.error(f"Error getting total pages: {e}")
            return 1

    def go_to_next_page(self) -> bool:
        """Navigate to next page in pagination, returns True if successful"""
        try:
            # Find and click next button
            next_button = self.driver.find_element(
                By.CSS_SELECTOR, "ul.pagination li.next:not(.disabled) a"
            )
            next_button.click()
            logger.info("Navigated to next page")
            time.sleep(3)  # Wait for page to load
            return True

        except NoSuchElementException:
            logger.info("No next page available or next button disabled")
            return False
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False

    def scrape_year(self, from_date: str, to_date: str) -> int:
        """
        Scrape orders for a specific year range
        Returns number of PDFs downloaded
        """
        year = from_date.split('-')[0]
        year_dir = os.path.join(self.DOWNLOAD_DIR, f"year_{year}")
        os.makedirs(year_dir, exist_ok=True)

        logger.info(f"Starting scrape for year {year} ({from_date} to {to_date})")

        # Navigate and search
        self.navigate_to_order_tab()
        self.fill_date_form(from_date, to_date)

        total_downloaded = 0
        current_page = 1

        # Get total pages (optional, for progress tracking)
        total_pages = self.get_total_pages()

        while True:
            logger.info(f"Processing page {current_page}/{total_pages}")

            # Get PDF links from current page
            pdf_links = self.get_pdf_links_from_page()

            if not pdf_links:
                logger.warning(f"No PDF links found on page {current_page}")
                break

            # Download each PDF
            for pdf_url, pdf_name in pdf_links:
                save_path = os.path.join(year_dir, pdf_name)

                # Skip if already downloaded
                if os.path.exists(save_path):
                    logger.info(f"Skipping {pdf_name} (already exists)")
                    continue

                if self.download_pdf(pdf_url, save_path):
                    total_downloaded += 1

                time.sleep(1)  # Be polite to the server

            # Try to go to next page
            if not self.go_to_next_page():
                break

            current_page += 1

        logger.info(f"Year {year} complete. Downloaded {total_downloaded} new PDFs")
        return total_downloaded

    def run(self, start_year: int = 2013):
        """Main method to run the scraper"""
        logger.info("="*60)
        logger.info("CCI Orders Scraper Started")
        logger.info("="*60)

        # Create base download directory
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

        # Generate date ranges
        date_ranges = self.generate_date_ranges(start_year)

        total_pdfs = 0

        try:
            for from_date, to_date in date_ranges:
                year_pdfs = self.scrape_year(from_date, to_date)
                total_pdfs += year_pdfs

                # Small delay between years
                time.sleep(2)

            logger.info("="*60)
            logger.info(f"Scraping complete! Total PDFs downloaded: {total_pdfs}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Scraper error: {e}", exc_info=True)
        finally:
            self.close()

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")


def main():
    """Main entry point"""
    scraper = CCIScraper(headless=True)

    try:
        scraper.run(start_year=2013)
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
