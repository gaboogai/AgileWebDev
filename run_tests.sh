#!/bin/bash

# Make sure Flask is not running
pkill -f "flask run" || true

# Set up the environment for testing
export FLASK_APP=server.py
export FLASK_ENV=testing
export SECRET_KEY=testing_secret_key

# Install test dependencies
pip install -r requirements.txt
pip install pytest selenium webdriver-manager

# Create test directory if it doesn't exist
mkdir -p tests

# Run individual tests with increased verbosity and detailed error messages
echo "Running test_app.py..."
python -m pytest -v test_app.py -s

echo "Running test_advanced.py..."
python -m pytest -v test_advanced.py -s

# Output the results
echo "Tests completed!"