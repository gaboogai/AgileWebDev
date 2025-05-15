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
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from app import app, db
from app.models import User, Song, Review, ReviewShares
from werkzeug.security import generate_password_hash

class TestAdvancedFeatures:
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
        chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Setup WebDriver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Create the database and the database tables
        with app.app_context():
            # Drop all tables first to ensure a clean state
            db.drop_all()
            db.create_all()
            
            # Create test users
            test_user1 = User(username='user1', password=generate_password_hash('password1'))
            test_user2 = User(username='user2', password=generate_password_hash('password2'))
            db.session.add(test_user1)
            db.session.add(test_user2)
            
            # Create test songs
            song1 = Song(title='Share Test Song', artist='Share Test Artist')
            song2 = Song(title='Another Test Song', artist='Another Test Artist')
            db.session.add(song1)
            db.session.add(song2)
            
            db.session.commit()
            
            # Create reviews for user1
            review1 = Review(rating=5, comment='Excellent song!', username='user1', song_id=1)
            review2 = Review(rating=3, comment='Decent song', username='user1', song_id=2)
            db.session.add(review1)
            db.session.add(review2)
            
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
        time.sleep(1)
        
        # Set the base URL with the dynamic port
        self.base_url = f"http://localhost:{self.port}"
        
        yield
        
        # Teardown
        self.driver.quit()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def login_user(self, username, password):
        """Helper method to login a user"""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.NAME, "submit").click()
        self.wait.until(EC.url_contains("dashboard"))
    
    def test_share_review(self):
        """Test sharing a review with another user"""
        # Login as user1
        self.login_user('user1', 'password1')
        
        # Go to share page
        self.driver.get(f"{self.base_url}/share")
        
        # Select a review to share
        select_element = Select(self.driver.find_element(By.ID, "review"))
        select_element.select_by_index(0)  # Select first review
        
        # Enter recipient username
        self.driver.find_element(By.ID, "recipient_username").send_keys("user2")
        
        # Submit the form
        self.driver.find_element(By.NAME, "submit").click()
        
        # Check if success message is displayed
        flash_message = self.driver.find_element(By.CLASS_NAME, "alert-success")
        assert "Review shared successfully" in flash_message.text
    
    def test_duplicate_username_error(self):
        """Test error handling for duplicate username during registration"""
        self.driver.get(f"{self.base_url}/register")
        
        # Try to register with an existing username
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("newpassword")
        self.driver.find_element(By.ID, "confirm_password").send_keys("newpassword")
        self.driver.find_element(By.ID, "submit").click()
        
        # Check if error message is displayed
        error_message = self.driver.find_element(By.CLASS_NAME, "text-danger")
        assert "Username already exists" in error_message.text
    
    def test_password_mismatch_error(self):
        """Test error handling for password mismatch during registration"""
        self.driver.get(f"{self.base_url}/register")
        
        # Try to register with mismatched passwords
        self.driver.find_element(By.ID, "username").send_keys("newuser")
        self.driver.find_element(By.ID, "password").send_keys("password1")
        self.driver.find_element(By.ID, "confirm_password").send_keys("password2")
        self.driver.find_element(By.ID, "submit").click()
        
        # Check if error message is displayed
        error_message = self.driver.find_element(By.CLASS_NAME, "text-danger")
        assert "Passwords must match" in error_message.text