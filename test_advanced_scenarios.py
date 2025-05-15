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
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
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
            
            # Use JavaScript to select the 5-star review (the review for the Rock Test Song)
            self.driver.execute_script("""
                document.getElementById('review').value = document.getElementById('review').options[0].value;
            """)
            
            # Enter recipient username
            recipient_field = self.driver.find_element(By.ID, "recipient_username")
            recipient_field.clear()
            recipient_field.send_keys("receiver")
            
            # Submit the form using JavaScript
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Check if success message is displayed
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))
            flash_message = self.driver.find_element(By.CLASS_NAME, "alert-success")
            assert "Review shared successfully" in flash_message.text
            
            # Logout
            self.driver.get(f"{self.base_url}/logout")
            self.wait.until(EC.url_contains("login"))
            
            # Step 2: Second user logs in and checks shared reviews
            self.login_user('receiver', 'password2')
            
            # Navigate to shared reviews page
            self.driver.get(f"{self.base_url}/shared-reviews")
            self.driver.save_screenshot("shared_reviews_receiver.png")
            
            # Check if the shared review is displayed
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
            shared_review_table = self.driver.find_element(By.TAG_NAME, "tbody")
            table_content = shared_review_table.text
            
            # The shared review should contain the Rock Test Song and sender's username
            assert "Rock Test Song" in table_content, "Shared song not found in shared reviews"
            assert "sender" in table_content, "Sender username not found in shared reviews"
            
            logger.info("test_share_and_receive_review passed")
            
        except Exception as e:
            self.driver.save_screenshot("share_receive_error.png")
            logger.error(f"Error in test_share_and_receive_review: {str(e)}")
            raise
    
    def test_multi_step_workflow(self):
        """Test a complex multi-step workflow: search -> add -> review -> share -> logout -> login as receiver -> view shared"""
        logger.info("Running test_multi_step_workflow")
        
        # Step 1: First user logs in
        self.login_user('sender', 'password1')
        
        try:
            # Step 2: Search for a non-existent song
            self.driver.find_element(By.LINK_TEXT, "Search Music").click()
            self.wait.until(EC.visibility_of_element_located((By.ID, "query")))
            
            search_term = "Advanced Workflow Test Song"
            self.driver.find_element(By.ID, "query").send_keys(search_term)
            
            # Click search button
            search_button = self.driver.find_element(By.CLASS_NAME, "btn-primary")
            self.driver.execute_script("arguments[0].click();", search_button)
            
            # Step 3: Add the new song
            self.wait.until(EC.visibility_of_element_located((By.ID, "artist")))
            self.driver.find_element(By.ID, "artist").send_keys("Advanced Workflow Artist")
            self.driver.find_element(By.ID, "title").send_keys(search_term)
            
            add_button = self.driver.find_element(By.CLASS_NAME, "btn-success")
            self.driver.execute_script("arguments[0].click();", add_button)
            
            # Step 4: Review the new song
            self.wait.until(EC.visibility_of_element_located((By.XPATH, f"//h3[contains(text(), '{search_term}')]")))
            
            rating_select = Select(self.driver.find_element(By.ID, "rating"))
            rating_select.select_by_visible_text("★★★★★ (5 stars)")
            
            comment_field = self.driver.find_element(By.ID, "comment")
            test_comment = "This is a multi-step advanced workflow test review"
            comment_field.send_keys(test_comment)
            
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Step 5: Share the new review
            self.wait.until(EC.url_contains("my-reviews"))
            self.driver.get(f"{self.base_url}/share")
            
            self.wait.until(EC.visibility_of_element_located((By.ID, "recipient_username")))
            
            # We need to get the option for our newly created review
            # The page is likely to have our new review as the first option
            select_element = self.driver.find_element(By.ID, "review")
            options = select_element.find_elements(By.TAG_NAME, "option")
            
            # Find the option that contains our search term
            new_review_option = None
            for option in options:
                if search_term in option.text:
                    new_review_option = option
                    break
                    
            assert new_review_option is not None, "Could not find the newly created review in the share options"
            
            # Select the option using JavaScript
            self.driver.execute_script("arguments[0].selected = true;", new_review_option)
            
            # Enter recipient username
            recipient_field = self.driver.find_element(By.ID, "recipient_username")
            recipient_field.clear()
            recipient_field.send_keys("receiver")
            
            # Submit the form
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Step 6: Verify success and logout
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))
            flash_message = self.driver.find_element(By.CLASS_NAME, "alert-success")
            assert "Review shared successfully" in flash_message.text
            
            self.driver.get(f"{self.base_url}/logout")
            self.wait.until(EC.url_contains("login"))
            
            # Step 7: Login as receiver and check shared reviews
            self.login_user('receiver', 'password2')
            
            self.driver.get(f"{self.base_url}/shared-reviews")
            self.driver.save_screenshot("advanced_workflow_shared.png")
            
            # Check if our shared review is displayed
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
            shared_review_table = self.driver.find_element(By.TAG_NAME, "tbody")
            table_content = shared_review_table.text
            
            assert search_term in table_content, "Newly created and shared song not found in shared reviews"
            assert test_comment in table_content, "Review comment not found in shared reviews"
            assert "sender" in table_content, "Sender username not found in shared reviews"
            
            logger.info("test_multi_step_workflow passed")
            
        except Exception as e:
            self.driver.save_screenshot("multi_step_workflow_error.png")
            logger.error(f"Error in test_multi_step_workflow: {str(e)}")
            raise