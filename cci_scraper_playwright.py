#!/usr/bin/env python3
"""
CCI Orders Scraper using Playwright
Downloads orders from Competition Commission of India website
URL: https://www.cci.gov.in/antitrust/orders

Playwright is more reliable in containerized environments than Selenium
"""

import os
import time
import logging
import asyncio
from datetime import datetime
from typing import List, Tuple
import requests
from playwright.async_api import async_playwright, Page, Browser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cci_scraper_playwright.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CCIScraperPlaywright:
    """Scraper for CCI orders using Playwright"""

    BASE_URL = "https://www.cci.gov.in/antitrust/orders#tab-2a"
    DOWNLOAD_DIR = "orders"

    def __init__(self, headless: bool = True):
        """Initialize the scraper"""
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    async def init_browser(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()

        logger.info("Launching Playwright Chromium browser...")
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
                '--disable-gpu'
            ]
        )

        # Create context with custom settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            ignore_https_errors=True  # Handle SSL issues
        )

        self.page = await self.context.new_page()
        logger.info("Browser initialized successfully")

    def generate_date_ranges(self, start_year: int = 2013) -> List[Tuple[str, str]]:
        """
        Generate year-by-year date ranges from start_year to current date
        Returns list of tuples (from_date, to_date) in format YYYY-MM-DD
        """
        current_date = datetime.now()
        current_year = current_date.year

        date_ranges = []

        for year in range(start_year, current_year + 1):
            if year == start_year:
                from_date = f"{year}-11-15"
            else:
                from_date = f"{year}-01-01"

            if year == current_year:
                to_date = current_date.strftime("%Y-%m-%d")
            else:
                to_date = f"{year}-12-31"

            date_ranges.append((from_date, to_date))
            logger.info(f"Generated date range: {from_date} to {to_date}")

        return date_ranges

    async def navigate_to_order_tab(self):
        """Navigate to the orders page and click on the order date tab"""
        logger.info(f"Navigating to {self.BASE_URL}")
        await self.page.goto(self.BASE_URL, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(3)

        try:
            # Click on the order date tab
            tab_selector = 'a[href="#tab-2a"]'
            await self.page.click(tab_selector, timeout=10000)
            logger.info("Clicked on order date tab")
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"Tab already active or error clicking: {e}")

    async def fill_date_form(self, from_date: str, to_date: str):
        """Fill the date form with from and to dates"""
        logger.info(f"Filling date form: {from_date} to {to_date}")

        try:
            # Fill from date
            await self.page.fill('#fromdate', from_date)
            await asyncio.sleep(0.5)

            # Fill to date
            await self.page.fill('#todate', to_date)
            await asyncio.sleep(0.5)

            # Click search button
            await self.page.click('#btn-filter-order')
            logger.info("Clicked search button")

            # Wait for results to load
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error filling date form: {e}")
            raise

    async def get_pdf_links_from_page(self) -> List[Tuple[str, str]]:
        """
        Extract PDF links from the current page
        Returns list of tuples (pdf_url, pdf_name)
        """
        pdf_links = []

        try:
            # Wait for table to be present
            await self.page.wait_for_selector('table', timeout=10000)

            # Get all PDF links
            links = await self.page.query_selector_all('a[href*=".pdf"]')

            for link in links:
                href = await link.get_attribute('href')
                if href:
                    # Make absolute URL if needed
                    if not href.startswith('http'):
                        href = f"https://www.cci.gov.in{href}" if href.startswith('/') else f"https://www.cci.gov.in/{href}"

                    pdf_name = href.split('/')[-1]
                    if not pdf_name.endswith('.pdf'):
                        pdf_name += '.pdf'

                    pdf_links.append((href, pdf_name))

            logger.info(f"Found {len(pdf_links)} PDF links on current page")

        except Exception as e:
            logger.error(f"Error extracting PDF links: {e}")

        return pdf_links

    def download_pdf(self, pdf_url: str, save_path: str, max_retries: int = 3) -> bool:
        """Download a PDF file with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {pdf_url} (attempt {attempt + 1}/{max_retries})")

                response = requests.get(pdf_url, timeout=30, stream=True, verify=False)
                response.raise_for_status()

                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logger.info(f"Successfully downloaded: {save_path}")
                return True

            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to download {pdf_url} after {max_retries} attempts")

        return False

    async def get_total_pages(self) -> int:
        """Get total number of pages from pagination"""
        try:
            pagination = await self.page.query_selector('ul.pagination')
            if not pagination:
                logger.info("No pagination found, assuming single page")
                return 1

            page_items = await pagination.query_selector_all('li')
            page_numbers = []

            for item in page_items:
                text = await item.inner_text()
                text = text.strip()
                if text.isdigit():
                    page_numbers.append(int(text))

            total_pages = max(page_numbers) if page_numbers else 1
            logger.info(f"Total pages found: {total_pages}")
            return total_pages

        except Exception as e:
            logger.error(f"Error getting total pages: {e}")
            return 1

    async def go_to_next_page(self) -> bool:
        """Navigate to next page in pagination, returns True if successful"""
        try:
            # Find and click next button
            next_button = await self.page.query_selector('ul.pagination li.next:not(.disabled) a')
            if next_button:
                await next_button.click()
                logger.info("Navigated to next page")
                await asyncio.sleep(3)
                return True
            else:
                logger.info("No next page available")
                return False

        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False

    async def scrape_year(self, from_date: str, to_date: str) -> int:
        """
        Scrape orders for a specific year range
        Returns number of PDFs downloaded
        """
        year = from_date.split('-')[0]
        year_dir = os.path.join(self.DOWNLOAD_DIR, f"year_{year}")
        os.makedirs(year_dir, exist_ok=True)

        logger.info(f"Starting scrape for year {year} ({from_date} to {to_date})")

        # Navigate and search
        await self.navigate_to_order_tab()
        await self.fill_date_form(from_date, to_date)

        total_downloaded = 0
        current_page = 1

        # Get total pages
        total_pages = await self.get_total_pages()

        while True:
            logger.info(f"Processing page {current_page}/{total_pages}")

            # Get PDF links from current page
            pdf_links = await self.get_pdf_links_from_page()

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

                time.sleep(1)

            # Try to go to next page
            if not await self.go_to_next_page():
                break

            current_page += 1

        logger.info(f"Year {year} complete. Downloaded {total_downloaded} new PDFs")
        return total_downloaded

    async def run(self, start_year: int = 2013):
        """Main method to run the scraper"""
        logger.info("="*60)
        logger.info("CCI Orders Scraper (Playwright) Started")
        logger.info("="*60)

        # Create base download directory
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

        # Initialize browser
        await self.init_browser()

        # Generate date ranges
        date_ranges = self.generate_date_ranges(start_year)

        total_pdfs = 0

        try:
            for from_date, to_date in date_ranges:
                year_pdfs = await self.scrape_year(from_date, to_date)
                total_pdfs += year_pdfs
                await asyncio.sleep(2)

            logger.info("="*60)
            logger.info(f"Scraping complete! Total PDFs downloaded: {total_pdfs}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Scraper error: {e}", exc_info=True)
        finally:
            await self.close()

    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")


async def main():
    """Main entry point"""
    scraper = CCIScraperPlaywright(headless=True)

    try:
        await scraper.run(start_year=2013)
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    asyncio.run(main())
