#!/usr/bin/env python3
"""
CCI Orders Scraper (requests-based version)
Downloads orders from Competition Commission of India website
URL: https://www.cci.gov.in/antitrust/orders

This version uses requests + BeautifulSoup instead of Selenium
to work in environments where headless Chrome is not available.
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cci_scraper_requests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CCIScraperRequests:
    """Scraper for CCI orders using requests instead of Selenium"""

    BASE_URL = "https://www.cci.gov.in/antitrust/orders"
    DOWNLOAD_DIR = "orders"

    def __init__(self):
        """Initialize the scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

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

    def search_orders(self, from_date: str, to_date: str, page: int = 1) -> dict:
        """
        Search for orders using the CCI website API/form
        Returns dict with orders data and pagination info
        """
        logger.info(f"Searching orders: {from_date} to {to_date}, page {page}")

        # First, get the main page to establish session
        try:
            response = self.session.get(self.BASE_URL, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to load main page: {e}")
            return {"orders": [], "total_pages": 0}

        # The website likely uses AJAX or form submission
        # We need to analyze the actual request the website makes
        # For now, let's try to fetch the page with date parameters

        params = {
            'fromdate': from_date,
            'todate': to_date,
            'page': page
        }

        try:
            # Try GET request with parameters
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract PDF links
            orders = []
            pdf_links = soup.find_all('a', href=lambda href: href and '.pdf' in href.lower())

            for link in pdf_links:
                pdf_url = link.get('href')
                if not pdf_url.startswith('http'):
                    pdf_url = f"https://www.cci.gov.in{pdf_url}" if pdf_url.startswith('/') else f"https://www.cci.gov.in/{pdf_url}"

                pdf_name = pdf_url.split('/')[-1]
                if not pdf_name.endswith('.pdf'):
                    pdf_name += '.pdf'

                orders.append({
                    'url': pdf_url,
                    'name': pdf_name
                })

            # Extract pagination info
            total_pages = 1
            pagination = soup.find('ul', class_='pagination')
            if pagination:
                page_items = pagination.find_all('li')
                page_numbers = []
                for item in page_items:
                    text = item.get_text().strip()
                    if text.isdigit():
                        page_numbers.append(int(text))
                if page_numbers:
                    total_pages = max(page_numbers)

            logger.info(f"Found {len(orders)} orders on page {page}/{total_pages}")

            return {
                'orders': orders,
                'total_pages': total_pages
            }

        except Exception as e:
            logger.error(f"Error searching orders: {e}")
            return {"orders": [], "total_pages": 0}

    def download_pdf(self, pdf_url: str, save_path: str, max_retries: int = 3) -> bool:
        """Download a PDF file with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {pdf_url} (attempt {attempt + 1}/{max_retries})")

                response = self.session.get(pdf_url, timeout=30, stream=True)
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

    def scrape_year(self, from_date: str, to_date: str) -> int:
        """
        Scrape orders for a specific year range
        Returns number of PDFs downloaded
        """
        year = from_date.split('-')[0]
        year_dir = os.path.join(self.DOWNLOAD_DIR, f"year_{year}")
        os.makedirs(year_dir, exist_ok=True)

        logger.info(f"Starting scrape for year {year} ({from_date} to {to_date})")

        total_downloaded = 0
        page = 1

        while True:
            result = self.search_orders(from_date, to_date, page)
            orders = result.get('orders', [])
            total_pages = result.get('total_pages', 1)

            if not orders:
                logger.warning(f"No orders found on page {page}")
                if page == 1:
                    logger.warning(f"No orders found for period {from_date} to {to_date}")
                break

            # Download each PDF
            for order in orders:
                pdf_url = order['url']
                pdf_name = order['name']
                save_path = os.path.join(year_dir, pdf_name)

                # Skip if already downloaded
                if os.path.exists(save_path):
                    logger.info(f"Skipping {pdf_name} (already exists)")
                    continue

                if self.download_pdf(pdf_url, save_path):
                    total_downloaded += 1

                time.sleep(1)  # Be polite to the server

            # Move to next page
            if page >= total_pages:
                break

            page += 1
            time.sleep(2)

        logger.info(f"Year {year} complete. Downloaded {total_downloaded} new PDFs")
        return total_downloaded

    def run(self, start_year: int = 2013):
        """Main method to run the scraper"""
        logger.info("="*60)
        logger.info("CCI Orders Scraper (Requests-based) Started")
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
                time.sleep(2)

            logger.info("="*60)
            logger.info(f"Scraping complete! Total PDFs downloaded: {total_pdfs}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Scraper error: {e}", exc_info=True)


def main():
    """Main entry point"""
    scraper = CCIScraperRequests()

    try:
        scraper.run(start_year=2013)
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
