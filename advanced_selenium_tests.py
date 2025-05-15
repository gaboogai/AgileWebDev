import os
import pytest
import tempfile
import time
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
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
        app.config['SECRET_KEY'] = 'test_secret_key'
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        with app.app_context():
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
            
            review1 = Review(rating=5, comment='Excellent song!', username='user1', song_id=song1.id)
            review2 = Review(rating=3, comment='Decent song', username='user1', song_id=song2.id)
            db.session.add(review1)
            db.session.add(review2)
            
            db.session.commit()
        
        self.server_thread = app.test_client()
        
        self.base_url = 'http://localhost:5000'
        
        yield
        
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
        self.login_user('user1', 'password1')
        
        self.driver.get(f"{self.base_url}/share")
        
        select_element = Select(self.driver.find_element(By.ID, "review"))
        select_element.select_by_visible_text("Share Test Song - 5")
        
        self.driver.find_element(By.ID, "recipient_username").send_keys("user2")
        
        self.driver.find_element(By.NAME, "submit").click()
        
        flash_message = self.driver.find_element(By.CLASS_NAME, "alert-success")
        assert "Review shared successfully" in flash_message.text
        
        self.driver.get(f"{self.base_url}/logout")
        
        self.login_user('user2', 'password2')
        
        self.driver.get(f"{self.base_url}/shared-reviews")
        
        shared_review_table = self.driver.find_element(By.TAG_NAME, "tbody")
        assert "Share Test Song" in shared_review_table.text
        assert "Excellent song!" in shared_review_table.text
        assert "user1" in shared_review_table.text
    
    def test_duplicate_username_error(self):
        """Test error handling for duplicate username during registration"""
        self.driver.get(f"{self.base_url}/register")
        
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("newpassword")
        self.driver.find_element(By.ID, "confirm_password").send_keys("newpassword")
        self.driver.find_element(By.ID, "submit").click()
        
        error_message = self.driver.find_element(By.CLASS_NAME, "text-danger")
        assert "Username already exists" in error_message.text
    
    def test_password_mismatch_error(self):
        """Test error handling for password mismatch during registration"""
        self.driver.get(f"{self.base_url}/register")
        
        self.driver.find_element(By.ID, "username").send_keys("newuser")
        self.driver.find_element(By.ID, "password").send_keys("password1")
        self.driver.find_element(By.ID, "confirm_password").send_keys("password2")
        self.driver.find_element(By.ID, "submit").click()
        
        error_message = self.driver.find_element(By.CLASS_NAME, "text-danger")
        assert "Passwords must match" in error_message.text
    
    def test_invalid_login(self):
        """Test error handling for invalid login credentials"""
        self.driver.get(f"{self.base_url}/login")
        
        self.driver.find_element(By.ID, "username").send_keys("user1")
        self.driver.find_element(By.ID, "password").send_keys("wrongpassword")
        self.driver.find_element(By.NAME, "submit").click()
        
        flash_message = self.driver.find_element(By.CLASS_NAME, "alert-danger")
        assert "Invalid username or password" in flash_message.text
    
    def test_navigation_after_login(self):
        """Test navigation between pages after login"""
        self.login_user('user1', 'password1')
        
        self.driver.find_element(By.LINK_TEXT, "My Reviews").click()
        self.wait.until(EC.url_contains("my-reviews"))
        assert "My Reviews" in self.driver.title
        
        self.driver.find_element(By.LINK_TEXT, "Search Music").click()
        self.wait.until(EC.url_contains("search"))
        assert "Search Music" in self.driver.title
        
        self.driver.find_element(By.LINK_TEXT, "Shared Reviews").click()
        self.wait.until(EC.url_contains("shared-reviews"))
        assert "Reviews Shared With Me" in self.driver.title
    
    def test_logout(self):
        """Test logout functionality"""
        self.login_user('user1', 'password1')
        
        self.driver.find_element(By.LINK_TEXT, "Logout").click()
        
        self.wait.until(EC.url_contains("login"))
        assert "TUN'D" in self.driver.title