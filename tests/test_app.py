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
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from app import app, db
from app.models import User, Song, Review
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                Song(title='Test Song 1', artist='Test Artist 1'),
                Song(title='Test Song 2', artist='Test Artist 2')
            ]
            for song in test_songs:
                db.session.add(song)
                
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
    
    def test_homepage_redirect(self):
        """Test that homepage redirects to login page"""
        logger.info("Running test_homepage_redirect")
        self.driver.get(f"{self.base_url}/")
        self.wait.until(EC.title_contains("TUN'D"))
        assert "login" in self.driver.current_url
        logger.info("test_homepage_redirect passed")
    
    def test_register_user(self):
        """Test user registration functionality"""
        logger.info("Running test_register_user")
        
        self.driver.get(f"{self.base_url}/login")
        
        self.driver.save_screenshot("login_page.png")
        logger.info(f"Login page title: {self.driver.title}")
        
        assert "TUN'D" in self.driver.title
        
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, "username")))
            logger.info("Registration form is visible")
            
            register_header = self.driver.find_element(By.XPATH, "//h3[contains(text(), 'Register')]")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", register_header)
            
            username_field = self.driver.find_elements(By.ID, "username")[1]
            password_field = self.driver.find_elements(By.ID, "password")[1]
            confirm_field = self.driver.find_element(By.ID, "confirm_password")
            
            username_field.send_keys("newuser")
            password_field.send_keys("newpassword")
            confirm_field.send_keys("newpassword")
            
            submit_buttons = self.driver.find_elements(By.NAME, "submit")
            register_submit = submit_buttons[1]
            
            self.driver.execute_script("arguments[0].click();", register_submit)
            
            self.wait.until(EC.url_contains("dashboard"))
            assert "Dashboard" in self.driver.title
            logger.info("test_register_user passed")
            
        except Exception as e:
            self.driver.save_screenshot("registration_error.png")
            logger.error(f"Error in test_register_user: {str(e)}")
            raise