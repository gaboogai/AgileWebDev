#!/bin/bash

# Make sure Flask is not running
pkill -f "flask run" || true

# Set up the environment for testing
export FLASK_APP=server.py
export FLASK_ENV=testing
export SECRET_KEY=testing_secret_key

# Install test dependencies
pip install -r requirements.txt
pip install pytest selenium webdriver-manager pytest-html

# Create directory for screenshots if it doesn't exist
mkdir -p test_screenshots

# Run tests with detailed output and HTML report
echo "Running test_app.py..."
python -m pytest -v test_app.py -s --html=test_report.html

echo "Running test_advanced.py..."
python -m pytest -v test_advanced.py -s --html=test_report_advanced.html

# Output the results
echo "Tests completed! Check the HTML reports and screenshots for details."
echo "Screenshot files are saved in the project directory."