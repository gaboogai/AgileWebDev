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
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from app import app, db
from app.models import User, Song, Review, ReviewShares
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAdvancedFeatures:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Setup test database and Selenium WebDriver
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
        app.config['SECRET_KEY'] = 'test_secret_key'
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            test_user1 = User(username='user1', password=generate_password_hash('password1'))
            test_user2 = User(username='user2', password=generate_password_hash('password2'))
            db.session.add(test_user1)
            db.session.add(test_user2)
            
            song1 = Song(title='Share Test Song', artist='Share Test Artist')
            song2 = Song(title='Another Test Song', artist='Another Test Artist')
            db.session.add(song1)
            db.session.add(song2)
            
            db.session.commit()
            
            review1 = Review(rating=5, comment='Excellent song!', username='user1', song_id=1)
            review2 = Review(rating=3, comment='Decent song', username='user1', song_id=2)
            db.session.add(review1)
            db.session.add(review2)
            
            db.session.commit()
        
        def find_free_port():
            # Find a free port for the Flask app
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]
                
        self.port = find_free_port()
        
        def run_flask_app():
            # Run Flask app in a separate thread
            app.run(port=self.port, use_reloader=False)
            
        self.flask_thread = Thread(target=run_flask_app)
        self.flask_thread.daemon = True
        self.flask_thread.start()
        
        time.sleep(3)
        
        self.base_url = f"http://localhost:{self.port}"
        logger.info(f"Flask app running at {self.base_url}")
        
        yield
        
        self.driver.quit()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def login_user(self, username, password):
        """Helper method to login a user using JS click to avoid ElementClickInterceptedException"""
        logger.info(f"Attempting to login as {username}")
        self.driver.get(f"{self.base_url}/login")
        
        self.driver.save_screenshot(f"login_attempt_{username}.png")
        
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            
            self.driver.find_element(By.ID, "username").send_keys(username)
            self.driver.find_element(By.ID, "password").send_keys(password)
            
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            self.wait.until(EC.url_contains("dashboard"))
            logger.info(f"Successfully logged in as {username}")
            
        except Exception as e:
            self.driver.save_screenshot(f"login_error_{username}.png")
            logger.error(f"Error during login: {str(e)}")
            raise
    
    def test_share_review(self):
        """Test sharing a review with another user"""
        logger.info("Running test_share_review")
        
        self.login_user('user1', 'password1')
        
        self.driver.get(f"{self.base_url}/share")
        self.driver.save_screenshot("share_page.png")
        
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "recipient_username")))
            
            # Select the first review to share
            self.driver.execute_script("""
                document.getElementById('review').value = document.getElementById('review').options[0].value;
            """)
            
            recipient_field = self.driver.find_element(By.ID, "recipient_username")
            recipient_field.clear()
            recipient_field.send_keys("user2")
            
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for and check success message
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))
            flash_message = self.driver.find_element(By.CLASS_NAME, "alert-success")
            assert "Review shared successfully" in flash_message.text
            logger.info("test_share_review passed")
            
        except Exception as e:
            self.driver.save_screenshot("share_review_error.png")
            logger.error(f"Error in test_share_review: {str(e)}")
            raise
    
    def test_duplicate_username_error(self):
        """Test error handling for duplicate username during registration"""
        logger.info("Running test_duplicate_username_error")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.save_screenshot("duplicate_username_page.png")
        
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            
            # Fill registration form with duplicate username
            register_header = self.driver.find_element(By.XPATH, "//h3[contains(text(), 'Register')]")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", register_header)
            
            username_field = self.driver.find_elements(By.ID, "username")[1]
            password_field = self.driver.find_elements(By.ID, "password")[1]
            confirm_field = self.driver.find_element(By.ID, "confirm_password")
            
            username_field.send_keys("user1")
            password_field.send_keys("newpassword")
            confirm_field.send_keys("newpassword")
            
            submit_buttons = self.driver.find_elements(By.NAME, "submit")
            register_submit = submit_buttons[1]
            
            self.driver.execute_script("arguments[0].click();", register_submit)
            
            # Wait for and check error message
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "text-danger")))
            error_message = self.driver.find_element(By.CLASS_NAME, "text-danger")
            assert "Username already exists" in error_message.text
            logger.info("test_duplicate_username_error passed")
            
        except Exception as e:
            self.driver.save_screenshot("duplicate_username_error.png")
            logger.error(f"Error in test_duplicate_username_error: {str(e)}")
            raise
    
    def test_password_mismatch_error(self):
        """Test error handling for password mismatch during registration"""
        logger.info("Running test_password_mismatch_error")
        
        self.driver.get(f"{self.base_url}/login")
        self.driver.save_screenshot("password_mismatch_page.png")
        
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            
            # Fill registration form with mismatched passwords
            register_header = self.driver.find_element(By.XPATH, "//h3[contains(text(), 'Register')]")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", register_header)
            
            username_field = self.driver.find_elements(By.ID, "username")[1]
            password_field = self.driver.find_elements(By.ID, "password")[1]
            confirm_field = self.driver.find_element(By.ID, "confirm_password")
            
            username_field.send_keys("newuser")
            password_field.send_keys("password1")
            confirm_field.send_keys("password2")
            
            submit_buttons = self.driver.find_elements(By.NAME, "submit")
            register_submit = submit_buttons[1]
            
            self.driver.execute_script("arguments[0].click();", register_submit)
            
            # Wait for and check error message
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "text-danger")))
            error_message = self.driver.find_element(By.CLASS_NAME, "text-danger")
            assert "Passwords must match" in error_message.text
            logger.info("test_password_mismatch_error passed")
            
        except Exception as e:
            self.driver.save_screenshot("password_mismatch_error.png")
            logger.error(f"Error in test_password_mismatch_error: {str(e)}")
            raise