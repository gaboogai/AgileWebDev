TUN'D Application Testing Guidelines
Overview
This document provides guidelines for testing the TUN'D music review application using Selenium. It covers setup, test organization, best practices, and troubleshooting tips.
Test Structure
The test suite is organized into several specialized categories:

Basic Authentication Tests (test_app.py, test_advanced.py)

User registration and login
Error handling for invalid inputs
Logout functionality


Song Management Tests (test_song_management.py)

Searching for songs
Adding new songs
Handling duplicate song prevention


Review Functionality Tests (test_review_functionality.py)

Creating new reviews
Updating existing reviews
Rating validation


Dashboard and Navigation Tests (fixed_test_dashboard_navigation.py)

Dashboard statistics verification
Navigation between pages
Top rated songs list


Advanced User Scenarios (fixed_test_advanced_scenarios.py)

Multi-user review sharing
Complex multi-step interactions



Setup Instructions
Prerequisites

Python 3.7+
Chrome browser installed
pip (Python package installer)

Environment Setup

Create a virtual environment:
bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install required dependencies:
bashpip install -r requirements.txt
pip install pytest selenium webdriver-manager pytest-html

Set environment variables:
bashexport FLASK_APP=server.py
export FLASK_ENV=testing
export SECRET_KEY=testing_secret_key
On Windows:
bashset FLASK_APP=server.py
set FLASK_ENV=testing
set SECRET_KEY=testing_secret_key


Running Tests
Use the provided script to run all tests:
bash./fixed_run_all_tests.sh
Or run individual test categories:
bash# Basic tests
python -m pytest -v test_app.py test_advanced.py

# Song management tests
python -m pytest -v test_song_management.py

# Review functionality tests
python -m pytest -v test_review_functionality.py

# Dashboard and navigation tests
python -m pytest -v fixed_test_dashboard_navigation.py

# Advanced user scenarios
python -m pytest -v fixed_test_advanced_scenarios.py
Best Practices
Test Isolation

Each test should create its own database to avoid interference
Use db.drop_all() and db.create_all() to ensure a clean state
Fixtures with autouse=True streamline setup and teardown

Element Selection

Use IDs when available (most reliable)
Class names are the second preference
XPath should be a last resort
Favor find_element(By.ID, "element-id") over find_element_by_id("element-id")

Waiting

Always use explicit waits over implicit waits or time.sleep()
Example:
pythonwait = WebDriverWait(driver, 10)
element = wait.until(EC.visibility_of_element_located((By.ID, "element-id")))


Error Handling

Wrap test steps in try/except blocks
Take screenshots at failure points
Log detailed error messages
Example:
pythontry:
    # Test steps
except Exception as e:
    driver.save_screenshot("error.png")
    logger.error(f"Error details: {str(e)}")
    raise


Element Interaction

Use JavaScript execution for challenging elements:
pythondriver.execute_script("arguments[0].click();", element)

Clear input fields before sending keys:
pythonelement.clear()
element.send_keys("text")

For dropdowns, use the Select class:
pythonselect = Select(driver.find_element(By.ID, "dropdown-id"))
select.select_by_visible_text("Option Text")


Common Issues and Solutions
ElementClickInterceptedException
Problem: Element is covered by another element
Solution:

Use JavaScript to click: driver.execute_script("arguments[0].click();", element)
Scroll element into view: driver.execute_script("arguments[0].scrollIntoView(true);", element)
Increase window size: chrome_options.add_argument("--window-size=1920,1080")

NoSuchElementException
Problem: Element not found on page
Solution:

Add appropriate wait conditions
Check if element is in an iframe (need to switch to it)
Verify your selector is correct
Take a screenshot to see the page state: driver.save_screenshot("debug.png")

TimeoutException
Problem: Wait condition not satisfied within timeout period
Solution:

Increase wait timeout: WebDriverWait(driver, 20)
Check if the condition is appropriate (visibility vs. presence)
Verify the application behavior manually
Add logging to check the page state

StaleElementReferenceException
Problem: Element is no longer attached to the DOM
Solution:

Re-locate the element after page changes
Use explicit waits with appropriate conditions
Implement retry logic for fragile operations

SQLAlchemy Deprecation Warnings
Problem: Query.get() method is deprecated
Solution:

Suppress with export PYTHONWARNINGS="ignore::DeprecationWarning:sqlalchemy"
For permanent fix, update code to use Session.get() instead

Directory Structure
/
|-- app/                         # Application code
|-- tests/                       # Test files
|   |-- test_app.py              # Basic authentication tests
|   |-- test_advanced.py         # Advanced authentication tests
|   |-- test_song_management.py  # Song management tests
|   |-- test_review_functionality.py # Review functionality tests
|   |-- fixed_test_dashboard_navigation.py # Dashboard/navigation tests
|   |-- fixed_test_advanced_scenarios.py # Advanced user scenarios
|   |-- conftest.py              # Shared test fixtures
|-- test_screenshots/            # Directory for test screenshots
|-- fixed_run_all_tests.sh       # Script to run all tests
|-- requirements.txt             # Project dependencies
|-- server.py                    # Main application entry point
|-- TESTING.md                   # This testing documentation
Extending the Test Suite
Adding New Tests

Identify the appropriate test category
Create a new test method with a descriptive name
Follow the pattern of existing tests:

Setup (login, navigate to relevant page)
Action (interact with elements)
Assertion (verify expected outcomes)
Proper error handling



Creating New Test Categories

Create a new test file with appropriate name
Copy the basic structure from existing test files
Modify the setup fixture as needed
Implement test methods
Add to the run script

Troubleshooting Tips
Debugging Failed Tests

Check test logs and screenshots
Run tests in non-headless mode by commenting out:
python# chrome_options.add_argument("--headless")

Add more logging at key points
Add breakpoints or print statements

Browser Issues

Update Chrome and ChromeDriver
Clear browser cache and cookies
Try with different browser options

Test Stability

Avoid fixed waits (time.sleep())
Use unique, stable selectors
Add retry logic for flaky operations
Take environmental factors into account (CI/CD vs local)

Maintenance

Update tests when application UI changes
Review and update tests regularly
Add tests for new features
Remove tests for deprecated features

Conclusion
Following these guidelines will help create and maintain a robust test suite for the TUN'D application. Remember that testing is an ongoing process, and the test suite should evolve alongside the application.