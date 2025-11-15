#!/bin/bash
# Setup script for CCI Orders Scraper

echo "Setting up CCI Orders Scraper..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create orders directory
echo "Creating orders directory..."
mkdir -p orders

echo ""
echo "Setup complete!"
echo ""
echo "To run the scraper:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the scraper: python cci_scraper.py"
echo ""
echo "Note: Make sure Chrome browser is installed on your system."
