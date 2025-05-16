# TUN'D

## Description
TUN'D is a music review platform. Our website gives users a centralised place to record their feelings about songs and store a permenant record of music they have listened to.
Our website also offers analysis of these reviews by sharing the top songs reviewed and data about users reviews.
On top of this users can share their reviews with other users creating a network to explore music.

## Use
Users first need to register for the site. These details can be used to log in at later points
Reviews are created by first searching for the song to see if someone else has already reviewed it (if not you can be the first to add it).
After this the user can input their review and a rating of the song.
Sharing can be done by selecting from the drop down menu of created reviews and then entering the username of the user to share it with.
To see analysis of these reviews simply check the dashboard of the site. 

## Directory Structure

The project is organized as follows:

### Main Application
- **app/** - Main application package
  - **static/** - Static files (CSS, JavaScript)
    - `button.js` - JavaScript for button functionality
    - `style_Main.css` - Main CSS styling
  - **templates/** - HTML templates
    - `base.html` - Base template with navigation structure
    - `base_login.html` - Base template for login/register page
    - `dashboard.html` - Dashboard template
    - `login.html` - Login/register template
    - `my_reviews.html` - User reviews template
    - `review.html` - Add/edit review template
    - `search.html` - Search template
    - `share.html` - Review sharing template
    - `shared_reviews.html` - Shared reviews template
  - `__init__.py` - Flask application initialization
  - `commands.py` - Flask CLI commands
  - `forms.py` - Form definitions using Flask-WTF
  - `models.py` - Database models
  - `routes.py` - Route definitions and handlers

### Database
- **migrations/** - Database migration files
  - **versions/** - Migration version scripts
    - `1afb4f2625e5_initial.py` - Initial migration
    - `305e7a5ceb01_reviewshares_table.py` - ReviewShares table migration
    - `f3c0a0e799f7_username_col.py` - Username column migration
  - `alembic.ini` - Alembic configuration
  - `env.py` - Migration environment
  - `script.py.mako` - Template for migration scripts

### Testing
- **assets/** - Additional assets for testing
  - `style.css` - Testing report styles
- `conftest.py` - Pytest configuration and fixtures
- `run_tests.sh` - Test execution script
- `test_app.py` - Basic authentication tests
- `test_advanced.py` - Advanced authentication tests
- `test_advanced_scenarios.py` - Multi-user interaction tests
- `test_dashboard_navigation.py` - UI navigation tests
- `test_review_functionality.py` - Review feature tests
- `test_song_management.py` - Song management tests
- `testing_guidelines.md` - Documentation for test suite

### Configuration
- `.flaskenv` - Flask environment variables
- `.gitignore` - Git ignore rules
- `requirements.txt` - Project dependencies
- `README.md` - Project documentation
- `server.py` - Application entry point

## Group Members
| ID       | Name           | github username |
| -------- | -------------- | --------------- |
| 23418094 | Michael Millar | gaboogai        |
| 24256619 | Danny Nguyen   | DannyNguyen5104 |
| 23860508 | Samay Gupta    | samo-e          |

# Launching the Application

## Guide for Using Venv
First you need to have python and pip installed

### First Install, Create and Activate Venv
```bash
sudo apt-get install python3-venv
```

To create a virtual environment run
```bash
python -m venv <venvname>
```

Now you need to activate the Virtual Environment:
To activate venv, for Windows:
```bash
.\venv\Scripts\activate
```
To activate venv, for Linux or Mac
```bash
source venv/bin/activate
```


### Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Deactivate
To Deactivate Venv once you have finished using
```bash
deactivate
```

## Running the site

The following command will initialise an empty database with the most up to date schema.
```bash
flask db upgrade
```
To then run the site, enter the following command.
```bash
flask run
```

## Testing

The testing is done automatically from the main directory using
```bash
./run_tests.sh
```
(if using a mac it may be needed to first give the testing scripts executable permissions using)
```bash
chmod +x run_tests.sh
```

After the tests are complete you will see some new html files created. 
Open those html files in your browser and you will see like a full report of the tests. 
It will also create some png displaying the website.