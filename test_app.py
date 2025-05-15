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
        
        # Start the Flask app
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Use http://localhost:5000 for testing
        self.base_url = 'http://localhost:5000'
        
        yield
        
        # Teardown
        self.driver.quit()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def test_homepage_redirect(self):
        """Test that homepage redirects to login page"""
        # Start Flask app in a separate thread
        from threading import Thread
        import socket
        
        def find_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]
        
        port = find_free_port()
        
        def run_flask_app():
            app.run(port=port, use_reloader=False)
        
        flask_thread = Thread(target=run_flask_app)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Give the app time to start
        time.sleep(1)
        
        self.base_url = f"http://localhost:{port}"
        
        self.driver.get(f"{self.base_url}/")
        assert "TUN'D" in self.driver.title
        assert "login" in self.driver.current_url
        
    def test_register_user(self):
        """Test user registration functionality"""
        # Start Flask app in a separate thread
        from threading import Thread
        import socket
        
        def find_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]
        
        port = find_free_port()
        
        def run_flask_app():
            app.run(port=port, use_reloader=False)
        
        flask_thread = Thread(target=run_flask_app)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Give the app time to start
        time.sleep(1)
        
        self.base_url = f"http://localhost:{port}"
        
        self.driver.get(f"{self.base_url}/register")
        
        # Fill out registration form
        self.driver.find_element(By.ID, "username").send_keys("newuser")
        self.driver.find_element(By.ID, "password").send_keys("newpassword")
        self.driver.find_element(By.ID, "confirm_password").send_keys("newpassword")
        self.driver.find_element(By.ID, "submit").click()
        
        # Check we're redirected to dashboard after successful registration
        self.wait.until(EC.url_contains("dashboard"))
        assert "Dashboard" in self.driver.title