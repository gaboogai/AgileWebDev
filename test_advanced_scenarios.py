import os
import pytest
import tempfile
import time
from threading import Thread
import socket
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from app import app, db
from app.models import User, Song, Review, ReviewShares
from werkzeug.security import generate_password_hash
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAdvancedUserScenarios:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Create a temporary file to isolate the database for each test
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
        app.config['SECRET_KEY'] = 'test_secret_key'
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        
        # Setup WebDriver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        # Create the database and the database tables
        with app.app_context():
            # Drop all tables first to ensure a clean state
            db.drop_all()
            db.create_all()
            
            # Add test users
            users = [
                User(username='sender', password=generate_password_hash('password1')),
                User(username='receiver', password=generate_password_hash('password2'))
            ]
            for user in users:
                db.session.add(user)
            
            # Add test songs - one for each genre to test filtering
            genres = ['Rock', 'Pop', 'Hip Hop', 'Jazz', 'Classical']
            for i, genre in enumerate(genres, 1):
                song = Song(title=f'{genre} Test Song', artist=f'{genre} Test Artist')
                db.session.add(song)
            
            db.session.commit()
            
            # Add reviews from the sender user for each song
            for i in range(1, 6):
                review = Review(rating=i, comment=f"Test rating {i}/5", username='sender', song_id=i)
                db.session.add(review)
            
            db.session.commit()
        
        # Find a free port for the Flask app
        def find_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]
                
        self.port = find_free_port()
        
        # Start Flask app in a separate thread
        def run_flask_app():
            app.run(port=self.port, use_reloader=False)
            
        self.flask_thread = Thread(target=run_flask_app)
        self.flask_thread.daemon = True
        self.flask_thread.start()
        
        # Give the app time to start
        time.sleep(3)
        
        # Set the base URL with the dynamic port
        self.base_url = f"http://localhost:{self.port}"
        logger.info(f"Flask app running at {self.base_url}")
        
        yield
        
        # Teardown
        self.driver.quit()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def login_user(self, username, password):
        """Helper method to login a specific user"""
        logger.info(f"Logging in as {username}")
        self.driver.get(f"{self.base_url}/login")
        
        try:
            # Wait for username field to be visible
            self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            
            # Fill out login form
            self.driver.find_element(By.ID, "username").send_keys(username)
            self.driver.find_element(By.ID, "password").send_keys(password)
            
            # Use JavaScript to click the submit button
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for redirection to dashboard
            self.wait.until(EC.url_contains("dashboard"))
            logger.info(f"Successfully logged in as {username}")
            
        except Exception as e:
            self.driver.save_screenshot(f"login_error_{username}.png")
            logger.error(f"Error during login: {str(e)}")
            raise
    
    def test_share_and_receive_review(self):
        """Test scenario: User shares a review and another user receives it"""
        logger.info("Running test_share_and_receive_review")
        
        # Step 1: First user logs in and shares a review
        self.login_user('sender', 'password1')
        
        try:
            # Navigate to share page
            self.driver.get(f"{self.base_url}/share")
            self.driver.save_screenshot("share_page_sender.png")
            
            # Wait for the page to load completely
            self.wait.until(EC.visibility_of_element_located((By.ID, "recipient_username")))
            
            # Check if the review select dropdown has options
            review_select = self.driver.find_element(By.ID, "review")
            options = review_select.find_elements(By.TAG_NAME, "option")
            logger.info(f"Found {len(options)} review options")
            
            # Make sure we have at least one review to share
            assert len(options) > 0, "No reviews available to share"
            
            # Use JavaScript to select the first option (review)
            self.driver.execute_script("""
                var select = document.getElementById('review');
                if (select && select.options.length > 0) {
                    select.selectedIndex = 0;
                }
            """)
            
            # Enter recipient username
            recipient_field = self.driver.find_element(By.ID, "recipient_username")
            recipient_field.clear()
            recipient_field.send_keys("receiver")
            
            # Submit the form using JavaScript
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Check if success message is displayed
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert")))
            flash_message = self.driver.find_element(By.CLASS_NAME, "alert").text
            logger.info(f"Flash message: {flash_message}")
            
            assert "Review shared successfully" in flash_message, f"Expected success message, got: {flash_message}"
            
            # Logout
            self.driver.get(f"{self.base_url}/logout")
            self.wait.until(EC.url_contains("login"))
            
            # Step 2: Second user logs in and checks shared reviews
            self.login_user('receiver', 'password2')
            
            # Navigate to shared reviews page
            self.driver.get(f"{self.base_url}/shared-reviews")
            self.driver.save_screenshot("shared_reviews_receiver.png")
            
            # Check for the presence of a table or message
            page_content = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Check if there's content in the shared reviews page
            if "No reviews have been shared with you yet" in page_content:
                logger.error("No shared reviews found - sharing may have failed")
                assert False, "No shared reviews found"
            
            # Look for a table with shared reviews
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            if len(tables) > 0:
                # There's a table, which means there are shared reviews
                table_content = tables[0].text
                logger.info(f"Table content: {table_content}")
                
                # Check for sender's username in the table
                assert "sender" in table_content, "Sender username not found in shared reviews"
                
                # Check for evidence of a song review
                assert "Test Song" in table_content or "rating" in table_content, "No evidence of a song review in shared reviews"
            else:
                # No table found, the test should fail
                logger.error("No table found in shared reviews page")
                self.driver.save_screenshot("no_table_found.png")
                assert False, "No table found in shared reviews page"
            
            logger.info("test_share_and_receive_review passed")
            
        except Exception as e:
            self.driver.save_screenshot("share_receive_error.png")
            logger.error(f"Error in test_share_and_receive_review: {str(e)}")
            raise