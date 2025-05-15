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
from webdriver_manager.chrome import ChromeDriverManager
from app import app, db
from app.models import User, Song, Review
from werkzeug.security import generate_password_hash

class TestApp:
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
            
            test_user = User(username='testuser', password=generate_password_hash('testpassword'))
            db.session.add(test_user)
            
            test_songs = [
                Song(title='Test Song 1', artist='Test Artist 1'),
                Song(title='Test Song 2', artist='Test Artist 2')
            ]
            for song in test_songs:
                db.session.add(song)
                
            db.session.commit()
        
        self.server_thread = app.test_client()
        
        self.base_url = 'http://localhost:5000'
        
        yield
        
        self.driver.quit()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def test_homepage_redirect(self):
        """Test that homepage redirects to login page"""
        self.driver.get(f"{self.base_url}/")
        assert "TUN'D" in self.driver.title
        assert "login" in self.driver.current_url
    
    def test_register_user(self):
        """Test user registration functionality"""
        self.driver.get(f"{self.base_url}/register")
        
        self.driver.find_element(By.ID, "username").send_keys("newuser")
        self.driver.find_element(By.ID, "password").send_keys("newpassword")
        self.driver.find_element(By.ID, "confirm_password").send_keys("newpassword")
        self.driver.find_element(By.ID, "submit").click()
        
        self.wait.until(EC.url_contains("dashboard"))
        assert "Dashboard" in self.driver.title
    
    def test_login_user(self):
        """Test user login functionality"""
        self.driver.get(f"{self.base_url}/login")
        
        self.driver.find_element(By.ID, "username").send_keys("testuser")
        self.driver.find_element(By.ID, "password").send_keys("testpassword")
        self.driver.find_element(By.NAME, "submit").click()
        
        self.wait.until(EC.url_contains("dashboard"))
        assert "Dashboard" in self.driver.title
    
    def test_search_music(self):
        """Test searching for music"""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.ID, "username").send_keys("testuser")
        self.driver.find_element(By.ID, "password").send_keys("testpassword")
        self.driver.find_element(By.NAME, "submit").click()
        
        self.driver.get(f"{self.base_url}/search")
        
        self.driver.find_element(By.ID, "query").send_keys("Test Song")
        self.driver.find_element(By.NAME, "submit").click()
        
        results = self.driver.find_elements(By.CLASS_NAME, "card-title")
        assert any("Test Song" in result.text for result in results)
    
    def test_add_song(self):
        """Test adding a new song"""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.ID, "username").send_keys("testuser")
        self.driver.find_element(By.ID, "password").send_keys("testpassword")
        self.driver.find_element(By.NAME, "submit").click()
        
        self.driver.get(f"{self.base_url}/search")
        
        self.driver.find_element(By.ID, "query").send_keys("New Test Song")
        self.driver.find_element(By.NAME, "submit").click()
        
        self.driver.find_element(By.ID, "artist").send_keys("New Test Artist")
        self.driver.find_element(By.ID, "title").send_keys("New Test Song")
        self.driver.find_element(By.NAME, "submit").click()
        
        self.wait.until(EC.url_contains("review"))
        
        song_title = self.driver.find_element(By.TAG_NAME, "h3").text
        assert "New Test Song" in song_title
    
    def test_review_song(self):
        """Test reviewing a song"""
        self.driver.get(f"{self.base_url}/login")
        self.driver.find_element(By.ID, "username").send_keys("testuser")
        self.driver.find_element(By.ID, "password").send_keys("testpassword")
        self.driver.find_element(By.NAME, "submit").click()
        
        with app.app_context():
            song_id = Song.query.filter_by(title='Test Song 1').first().id
            
        self.driver.get(f"{self.base_url}/review/{song_id}")
        
        self.driver.find_element(By.ID, "rating").send_keys("5")
        
        self.driver.find_element(By.ID, "comment").send_keys("This is a test review")
        
        self.driver.find_element(By.NAME, "submit").click()
        
        self.wait.until(EC.url_contains("my-reviews"))
        
        review_items = self.driver.find_elements(By.CLASS_NAME, "review-item")
        assert any("Test Song 1" in item.text for item in review_items)
        assert any("This is a test review" in item.text for item in review_items)