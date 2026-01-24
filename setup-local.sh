#!/bin/bash
set -e

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

echo ""
echo "Setup complete! To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To start LocalStack:"
echo "  docker-compose up -d"
echo ""
echo "To run the script:"
echo "  python create-riders-list.py"
