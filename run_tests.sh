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

# Fix for SQLAlchemy warnings - can be safely ignored
export PYTHONWARNINGS="ignore::DeprecationWarning:sqlalchemy"

# Run basic tests first (already working)
echo "Running basic tests (test_app.py and test_advanced.py)..."
python -m pytest -v test_app.py test_advanced.py -s --html=report_basic_tests.html

# Run the fixed test files
echo "Running dashboard and navigation tests (fixed_test_dashboard_navigation.py)..."
python -m pytest -v fixed_test_dashboard_navigation.py -s --html=report_dashboard_navigation.html

echo "Running advanced user scenarios tests (fixed_test_advanced_scenarios.py)..."
python -m pytest -v fixed_test_advanced_scenarios.py -s --html=report_advanced_scenarios.html

# Run song management and review functionality tests
echo "Running song management tests (test_song_management.py)..."
python -m pytest -v test_song_management.py -s --html=report_song_management.html

echo "Running review functionality tests (test_review_functionality.py)..."
python -m pytest -v test_review_functionality.py -s --html=report_review_functionality.html

# Output the results
echo "Tests completed! Check the HTML reports for details."
echo "Screenshot files are saved in the project directory."