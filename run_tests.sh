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

# Run the tests
python -m pytest -v selenium_test.py advselenium_test.py

# Output the results
echo "Tests completed!"