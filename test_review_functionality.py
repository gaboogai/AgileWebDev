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
from selenium.webdriver.support.ui import Select  # Added missing import
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from app import app, db
from app.models import User, Song, Review
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestReviewFunctionality:
    """Test class for review functionality"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database, webdriver, and Flask app"""
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
            
            test_user = User(username='testuser', password=generate_password_hash('testpassword'))
            db.session.add(test_user)
            
            test_songs = [
                Song(title='Song for Review', artist='Test Artist'),
                Song(title='Song to Update', artist='Test Artist')
            ]
            for song in test_songs:
                db.session.add(song)
                
            db.session.commit()
            
            existing_review = Review(rating=3, comment="Initial review", username='testuser', song_id=2)
            db.session.add(existing_review)
            db.session.commit()
        
        def find_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]
                
        self.port = find_free_port()
        
        def run_flask_app():
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
    
    def login_user(self):
        """Helper method to login as testuser"""
        logger.info("Logging in as testuser")
        self.driver.get(f"{self.base_url}/login")
        
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            
            self.driver.find_element(By.ID, "username").send_keys("testuser")
            self.driver.find_element(By.ID, "password").send_keys("testpassword")
            
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            self.wait.until(EC.url_contains("dashboard"))
            logger.info("Successfully logged in")
            
        except Exception as e:
            self.driver.save_screenshot("login_error.png")
            logger.error(f"Error during login: {str(e)}")
            raise
    
    def test_create_new_review(self):
        """Test creating a new review for a song"""
        logger.info("Running test_create_new_review")
        self.login_user()
        
        try:
            with app.app_context():
                song_id = Song.query.filter_by(title='Song for Review').first().id
                
            self.driver.get(f"{self.base_url}/review/{song_id}")
            self.driver.save_screenshot("review_page.png")
            
            self.wait.until(EC.visibility_of_element_located((By.ID, "rating")))
            
            rating_select = Select(self.driver.find_element(By.ID, "rating"))
            rating_select.select_by_visible_text("★★★★★ (5 stars)")
            
            comment_field = self.driver.find_element(By.ID, "comment")
            comment_field.send_keys("This is a great song! Test review.")
            
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            self.wait.until(EC.url_contains("my-reviews"))
            
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "review-item")))
            reviews = self.driver.find_elements(By.CLASS_NAME, "review-item")
            
            review_found = False
            for review in reviews:
                if "Song for Review" in review.text and "This is a great song! Test review." in review.text:
                    review_found = True
                    break
                    
            assert review_found, "New review was not found on the my-reviews page"
            logger.info("test_create_new_review passed")
            
        except Exception as e:
            self.driver.save_screenshot("create_review_error.png")
            logger.error(f"Error in test_create_new_review: {str(e)}")
            raise
    
    def test_update_existing_review(self):
        """Test updating an existing review"""
        logger.info("Running test_update_existing_review")
        self.login_user()
        
        try:
            with app.app_context():
                song_id = Song.query.filter_by(title='Song to Update').first().id
                
            self.driver.get(f"{self.base_url}/review/{song_id}")
            self.driver.save_screenshot("update_review_page.png")
            
            self.wait.until(EC.visibility_of_element_located((By.ID, "rating")))
            
            rating_value = self.driver.execute_script("return document.getElementById('rating').value;")
            comment_field = self.driver.find_element(By.ID, "comment")
            
            logger.info(f"Current rating value: {rating_value}")
            logger.info(f"Current comment value: {comment_field.get_attribute('value')}")
            
            if rating_value != "3":
                logger.warning(f"Expected rating 3, got {rating_value}")
            
            if comment_field.get_attribute("value") != "Initial review":
                logger.warning(f"Expected comment 'Initial review', got '{comment_field.get_attribute('value')}'")
            
            rating_select = Select(self.driver.find_element(By.ID, "rating"))
            rating_select.select_by_visible_text("★★★★☆ (4 stars)")
            
            comment_field.clear()
            comment_field.send_keys("Updated review - it's better than I initially thought!")
            
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            self.wait.until(EC.url_contains("my-reviews"))
            
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "review-item")))
            reviews = self.driver.find_elements(By.CLASS_NAME, "review-item")
            
            review_found = False
            for review in reviews:
                if "Song to Update" in review.text and "Updated review" in review.text:
                    review_found = True
                    break
                    
            assert review_found, "Updated review was not found on the my-reviews page"
            logger.info("test_update_existing_review passed")
            
        except Exception as e:
            self.driver.save_screenshot("update_review_error.png")
            logger.error(f"Error in test_update_existing_review: {str(e)}")
            raise
    
    def test_review_rating_validation(self):
        """Test that review ratings are properly constrained to the 1-5 range"""
        logger.info("Running test_review_rating_validation")
        self.login_user()
        
        try:
            with app.app_context():
                song_id = Song.query.filter_by(title='Song for Review').first().id
                
            self.driver.get(f"{self.base_url}/review/{song_id}")
            
            self.wait.until(EC.visibility_of_element_located((By.ID, "rating")))
            
            rating_select = Select(self.driver.find_element(By.ID, "rating"))
            options = rating_select.options
            
            assert len(options) == 5, "There should be exactly 5 rating options"
            
            option_values = [option.get_attribute("value") for option in options]
            logger.info(f"Rating option values: {option_values}")
            
            expected_values = ["5", "4", "3", "2", "1"]
            assert sorted(option_values) == sorted(expected_values), f"Rating options should be 1 to 5, but got {option_values}"
            logger.info("test_review_rating_validation passed")
            
        except Exception as e:
            self.driver.save_screenshot("rating_validation_error.png")
            logger.error(f"Error in test_review_rating_validation: {str(e)}")
            raise