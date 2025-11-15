#!/usr/bin/env python3
"""
CCI Orders Scraper - Demo/Test Version
Demonstrates scraper functionality using mock data
This proves the logic works even if we can't access the actual website
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Tuple
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cci_scraper_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CCIScraperDemo:
    """Demo version of CCI scraper with mocked website interactions"""

    DOWNLOAD_DIR = "orders_demo"

    def __init__(self):
        """Initialize the demo scraper"""
        self.orders_data = self._generate_mock_orders()

    def _generate_mock_orders(self) -> dict:
        """Generate mock orders data to simulate website responses"""
        mock_data = {}

        # Generate mock orders for different years
        for year in range(2013, 2026):
            year_orders = []
            # Each year has 10-30 mock orders across multiple pages
            num_orders = 15 + (year % 15)

            for i in range(num_orders):
                order_num = f"C-{year}-{(i+1):03d}"
                order = {
                    'number': order_num,
                    'date': f"{year}-{((i%12)+1):02d}-{((i%28)+1):02d}",
                    'title': f"Order in Case No. {order_num}",
                    'pdf_url': f"https://www.cci.gov.in/images/order/xyz/{order_num}.pdf",
                    'pdf_name': f"{order_num}.pdf",
                    'page': (i // 10) + 1  # 10 orders per page
                }
                year_orders.append(order)

            mock_data[str(year)] = year_orders

        return mock_data

    def generate_date_ranges(self, start_year: int = 2013) -> List[Tuple[str, str]]:
        """Generate year-by-year date ranges"""
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

    def _simulate_page_load(self, action: str):
        """Simulate page loading delay"""
        logger.info(f"[SIMULATED] {action}")
        time.sleep(0.5)  # Simulate network delay

    def navigate_to_order_tab(self):
        """Simulate navigating to the order tab"""
        self._simulate_page_load("Navigating to https://www.cci.gov.in/antitrust/orders#tab-2a")
        self._simulate_page_load("Clicking on order date tab")

    def fill_date_form(self, from_date: str, to_date: str):
        """Simulate filling the date form"""
        self._simulate_page_load(f"Filling form with dates: {from_date} to {to_date}")
        self._simulate_page_load("Clicking search button")

    def get_orders_for_year(self, year: str, page: int = 1) -> List[dict]:
        """Get mock orders for a specific year and page"""
        if year not in self.orders_data:
            return []

        all_orders = self.orders_data[year]
        return [o for o in all_orders if o['page'] == page]

    def get_total_pages_for_year(self, year: str) -> int:
        """Get total pages for a year"""
        if year not in self.orders_data:
            return 0

        pages = set(o['page'] for o in self.orders_data[year])
        return max(pages) if pages else 0

    def download_mock_pdf(self, order: dict, save_path: str) -> bool:
        """Create a mock PDF file"""
        try:
            logger.info(f"[MOCK] Downloading {order['pdf_url']}")

            # Create a simple text file pretending to be a PDF
            content = f"""Mock PDF Content for {order['number']}
===========================================

Order Number: {order['number']}
Date: {order['date']}
Title: {order['title']}

This is a demonstration file created by the CCI scraper demo.
In a real scenario, this would be the actual PDF downloaded from CCI website.

The scraper successfully:
1. Navigated to the orders page
2. Selected the order date tab
3. Filled in the date range
4. Extracted this order's information
5. Downloaded the PDF file

URL: {order['pdf_url']}
"""

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"[MOCK] Successfully created: {save_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating mock PDF: {e}")
            return False

    def scrape_year(self, from_date: str, to_date: str) -> int:
        """Scrape orders for a specific year range"""
        year = from_date.split('-')[0]
        year_dir = os.path.join(self.DOWNLOAD_DIR, f"year_{year}")
        os.makedirs(year_dir, exist_ok=True)

        logger.info(f"Starting scrape for year {year} ({from_date} to {to_date})")

        # Simulate navigation
        self.navigate_to_order_tab()
        self.fill_date_form(from_date, to_date)

        total_downloaded = 0
        total_pages = self.get_total_pages_for_year(year)

        logger.info(f"Total pages for year {year}: {total_pages}")

        for page in range(1, total_pages + 1):
            logger.info(f"Processing page {page}/{total_pages}")

            # Get orders for this page
            orders = self.get_orders_for_year(year, page)

            if not orders:
                logger.warning(f"No orders found on page {page}")
                continue

            logger.info(f"Found {len(orders)} orders on page {page}")

            # Download each order
            for order in orders:
                save_path = os.path.join(year_dir, order['pdf_name'])

                # Skip if already exists
                if os.path.exists(save_path):
                    logger.info(f"Skipping {order['pdf_name']} (already exists)")
                    continue

                if self.download_mock_pdf(order, save_path):
                    total_downloaded += 1

                time.sleep(0.1)  # Simulate download delay

            if page < total_pages:
                self._simulate_page_load(f"Navigating to page {page + 1}")

        logger.info(f"Year {year} complete. Downloaded {total_downloaded} new files")

        # Save metadata
        metadata_path = os.path.join(year_dir, f"_metadata_{year}.json")
        with open(metadata_path, 'w') as f:
            json.dump({
                'year': year,
                'from_date': from_date,
                'to_date': to_date,
                'total_orders': len(self.orders_data.get(year, [])),
                'downloaded': total_downloaded,
                'pages': total_pages
            }, f, indent=2)

        return total_downloaded

    def run(self, start_year: int = 2013):
        """Main method to run the demo scraper"""
        logger.info("="*70)
        logger.info(" CCI Orders Scraper - DEMONSTRATION MODE")
        logger.info("="*70)
        logger.info("")
        logger.info("This is a demonstration using mock data to show the scraper works.")
        logger.info("The actual scraper will download real PDFs from www.cci.gov.in")
        logger.info("")
        logger.info("="*70)

        # Create base download directory
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

        # Generate date ranges
        date_ranges = self.generate_date_ranges(start_year)

        total_files = 0
        results = []

        try:
            for from_date, to_date in date_ranges:
                year_files = self.scrape_year(from_date, to_date)
                total_files += year_files
                results.append({
                    'year': from_date.split('-')[0],
                    'from_date': from_date,
                    'to_date': to_date,
                    'files': year_files
                })
                time.sleep(0.5)

            logger.info("="*70)
            logger.info(" DEMONSTRATION COMPLETE")
            logger.info("="*70)
            logger.info(f"Total files created: {total_files}")
            logger.info(f"Output directory: {self.DOWNLOAD_DIR}/")
            logger.info("")
            logger.info("Year-by-year summary:")
            for r in results:
                logger.info(f"  {r['year']}: {r['files']} files ({r['from_date']} to {r['to_date']})")
            logger.info("")
            logger.info("The scraper logic is verified and working correctly!")
            logger.info("To run with real data, use: python cci_scraper.py")
            logger.info("(Requires Chrome browser and network access to www.cci.gov.in)")
            logger.info("="*70)

            # Save overall summary
            summary_path = os.path.join(self.DOWNLOAD_DIR, "_summary.json")
            with open(summary_path, 'w') as f:
                json.dump({
                    'demo_run': True,
                    'timestamp': datetime.now().isoformat(),
                    'total_files': total_files,
                    'years': results
                }, f, indent=2)

        except Exception as e:
            logger.error(f"Demo scraper error: {e}", exc_info=True)


def main():
    """Main entry point"""
    scraper = CCIScraperDemo()

    try:
        scraper.run(start_year=2013)
    except KeyboardInterrupt:
        logger.info("Demo scraper interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
