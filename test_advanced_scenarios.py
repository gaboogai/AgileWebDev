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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAdvancedUserScenarios:
    @pytest.fixture(autouse=True)
    def setup(self):
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
            
            users = [
                User(username='sender', password=generate_password_hash('password1')),
                User(username='receiver', password=generate_password_hash('password2'))
            ]
            for user in users:
                db.session.add(user)
            
            genres = ['Rock', 'Pop', 'Hip Hop', 'Jazz', 'Classical']
            for i, genre in enumerate(genres, 1):
                song = Song(title=f'{genre} Test Song', artist=f'{genre} Test Artist')
                db.session.add(song)
            
            db.session.commit()
            
            for i in range(1, 6):
                review = Review(rating=i, comment=f"Test rating {i}/5", username='sender', song_id=i)
                db.session.add(review)
            
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
        
        time.sleep(5)
        
        self.base_url = f"http://localhost:{self.port}"
        logger.info(f"Flask app running at {self.base_url}")
        
        yield
        
        self.driver.quit()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def login_user(self, username, password):
        """Helper method to login a specific user"""
        logger.info(f"Logging in as {username}")
        self.driver.get(f"{self.base_url}/login")
        
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
    
    def test_share_and_receive_review(self):
        """Test scenario: User shares a review and another user receives it"""
        logger.info("Running test_share_and_receive_review")
        
        self.login_user('sender', 'password1')
        
        try:
            self.driver.get(f"{self.base_url}/share")
            self.driver.save_screenshot("share_page_sender.png")
            
            self.wait.until(EC.visibility_of_element_located((By.ID, "recipient_username")))
            
            review_select = self.driver.find_element(By.ID, "review")
            options = review_select.find_elements(By.TAG_NAME, "option")
            logger.info(f"Found {len(options)} review options")
            
            if len(options) == 0:
                logger.error("No reviews available in dropdown")
                self.driver.save_screenshot("no_review_options.png")
                assert False, "No reviews available to share"
            
            self.driver.execute_script("""
                var select = document.getElementById('review');
                if (select && select.options.length > 0) {
                    select.selectedIndex = 0;
                    // Trigger change event
                    var event = new Event('change', { bubbles: true });
                    select.dispatchEvent(event);
                }
            """)
            
            try:
                review_select = Select(self.driver.find_element(By.ID, "review"))
                review_select.select_by_index(0)
            except Exception as e:
                logger.warning(f"Select fallback failed: {str(e)}")
            
            recipient_field = self.driver.find_element(By.ID, "recipient_username")
            recipient_field.clear()
            recipient_field.send_keys("receiver")
            
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert")))
            flash_message = self.driver.find_element(By.CLASS_NAME, "alert").text
            logger.info(f"Flash message: {flash_message}")
            
            assert "shared" in flash_message.lower(), f"Expected success message containing 'shared', got: {flash_message}"
            
            self.driver.get(f"{self.base_url}/logout")
            self.wait.until(EC.url_contains("login"))
            
            self.login_user('receiver', 'password2')
            
            self.driver.get(f"{self.base_url}/shared-reviews")
            self.driver.save_screenshot("shared_reviews_receiver.png")

            page_source = self.driver.page_source
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"Shared reviews page text: {page_text[:500]}...")
            
            if "No reviews have been shared with you yet" in page_text:
                logger.error("No shared reviews found - sharing failed")
                assert False, "No shared reviews found after sharing"
            
            logger.info("Shared review found on receiver's page")
            
            assert "sender" in page_text.lower(), "Sender username not found in shared reviews"
            
            logger.info("test_share_and_receive_review passed")
            
        except Exception as e:
            self.driver.save_screenshot("share_receive_error.png")
            logger.error(f"Error in test_share_and_receive_review: {str(e)}")
            raise