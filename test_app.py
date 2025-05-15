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
from selenium.common.exceptions import ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from app import app, db
from app.models import User, Song, Review
from werkzeug.security import generate_password_hash

class TestApp:
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
        chrome_options.add_argument("--window-size=1920,1080")  # Set window size
        chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
        
        # Setup WebDriver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Create the database and the database tables
        with app.app_context():
            # Drop all tables first to ensure a clean state
            db.drop_all()
            db.create_all()
            
            # Add test data
            test_user = User(username='testuser', password=generate_password_hash('testpassword'))
            db.session.add(test_user)
            
            test_songs = [
                Song(title='Test Song 1', artist='Test Artist 1'),
                Song(title='Test Song 2', artist='Test Artist 2')
            ]
            for song in test_songs:
                db.session.add(song)
                
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
        time.sleep(2)
        
        # Set the base URL with the dynamic port
        self.base_url = f"http://localhost:{self.port}"
        
        yield
        
        # Teardown
        self.driver.quit()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def test_homepage_redirect(self):
        """Test that homepage redirects to login page"""
        self.driver.get(f"{self.base_url}/")
        self.wait.until(EC.title_contains("TUN'D"))
        assert "login" in self.driver.current_url
    
    def test_register_user(self):
        """Test user registration functionality"""
        self.driver.get(f"{self.base_url}/register")
        
        # Wait for the registration form to be loaded
        username_field = self.wait.until(EC.element_to_be_clickable((By.NAME, "username")))
        password_field = self.wait.until(EC.element_to_be_clickable((By.NAME, "password")))
        confirm_field = self.wait.until(EC.element_to_be_clickable((By.NAME, "confirm_password")))
        
        # Fill out registration form
        username_field.send_keys("newuser")
        password_field.send_keys("newpassword")
        confirm_field.send_keys("newpassword")
        
        # Use JavaScript to click the element to avoid ElementClickInterceptedException
        submit_button = self.driver.find_element(By.NAME, "submit")
        self.driver.execute_script("arguments[0].click();", submit_button)
        
        # Check redirection
        self.wait.until(EC.url_contains("dashboard"))
        assert "Dashboard" in self.driver.title