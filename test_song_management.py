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

class TestSongManagement:
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
                Song(title='Existing Song', artist='Test Artist'),
                Song(title='Another Song', artist='Test Artist')
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
    
    def test_search_existing_song(self):
        """Test searching for an existing song"""
        logger.info("Running test_search_existing_song")
        self.login_user()
        
        try:
            self.driver.get(f"{self.base_url}/search")
            self.wait.until(EC.visibility_of_element_located((By.ID, "query")))
            
            self.driver.find_element(By.ID, "query").send_keys("Existing")
            
            search_button = self.driver.find_element(By.CLASS_NAME, "btn-primary")
            self.driver.execute_script("arguments[0].click();", search_button)
            
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "card-title")))
            results = self.driver.find_elements(By.CLASS_NAME, "card-title")
            assert any("Existing Song" in result.text for result in results)
            logger.info("test_search_existing_song passed")
            
        except Exception as e:
            self.driver.save_screenshot("search_error.png")
            logger.error(f"Error in test_search_existing_song: {str(e)}")
            raise
    
    def test_search_nonexistent_song(self):
        """Test searching for a song that doesn't exist"""
        logger.info("Running test_search_nonexistent_song")
        self.login_user()
        
        try:
            self.driver.get(f"{self.base_url}/search")
            self.wait.until(EC.visibility_of_element_located((By.ID, "query")))
            
            self.driver.find_element(By.ID, "query").send_keys("Nonexistent Song")
            
            search_button = self.driver.find_element(By.CLASS_NAME, "btn-primary")
            self.driver.execute_script("arguments[0].click();", search_button)
            
            self.wait.until(EC.visibility_of_element_located((By.XPATH, "//h4[contains(text(), 'Add New Song')]")))
            add_new_form = self.driver.find_element(By.XPATH, "//h4[contains(text(), 'Add New Song')]")
            assert add_new_form.is_displayed()
            logger.info("test_search_nonexistent_song passed")
            
        except Exception as e:
            self.driver.save_screenshot("search_nonexistent_error.png")
            logger.error(f"Error in test_search_nonexistent_song: {str(e)}")
            raise
    
    def test_add_new_song(self):
        """Test adding a new song"""
        logger.info("Running test_add_new_song")
        self.login_user()
        
        try:
            self.driver.get(f"{self.base_url}/search")
            self.wait.until(EC.visibility_of_element_located((By.ID, "query")))
            
            self.driver.find_element(By.ID, "query").send_keys("Brand New Song")
            
            search_button = self.driver.find_element(By.CLASS_NAME, "btn-primary")
            self.driver.execute_script("arguments[0].click();", search_button)
            
            self.wait.until(EC.visibility_of_element_located((By.ID, "artist")))
            self.driver.find_element(By.ID, "artist").send_keys("New Artist")
            self.driver.find_element(By.ID, "title").send_keys("Brand New Song")
            
            add_button = self.driver.find_element(By.CLASS_NAME, "btn-success")
            self.driver.execute_script("arguments[0].click();", add_button)
            
            self.wait.until(EC.visibility_of_element_located((By.XPATH, "//h3[contains(text(), 'Brand New Song')]")))
            song_title = self.driver.find_element(By.TAG_NAME, "h3").text
            assert "Brand New Song" in song_title
            logger.info("test_add_new_song passed")
            
        except Exception as e:
            self.driver.save_screenshot("add_song_error.png")
            logger.error(f"Error in test_add_new_song: {str(e)}")
            raise
    
    def test_add_duplicate_song(self):
        """Test trying to add a song that already exists"""
        logger.info("Running test_add_duplicate_song")
        self.login_user()
        
        try:
            self.driver.get(f"{self.base_url}/search")
            self.wait.until(EC.visibility_of_element_located((By.ID, "query")))
            
            self.driver.find_element(By.ID, "query").send_keys("Unique Term That Won't Match")
            
            search_button = self.driver.find_element(By.CLASS_NAME, "btn-primary")
            self.driver.execute_script("arguments[0].click();", search_button)
            
            self.wait.until(EC.visibility_of_element_located((By.ID, "artist")))
            self.driver.find_element(By.ID, "artist").send_keys("Test Artist")
            self.driver.find_element(By.ID, "title").send_keys("Existing Song")
            
            add_button = self.driver.find_element(By.CLASS_NAME, "btn-success")
            self.driver.execute_script("arguments[0].click();", add_button)
            
            self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert")))
            flash_message = self.driver.find_element(By.CLASS_NAME, "alert").text
            assert "This song already exists" in flash_message
            logger.info("test_add_duplicate_song passed")
            
        except Exception as e:
            self.driver.save_screenshot("add_duplicate_error.png")
            logger.error(f"Error in test_add_duplicate_song: {str(e)}")
            raise