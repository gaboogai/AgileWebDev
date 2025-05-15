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

class TestDashboardAndNavigation:
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
                Song(title='Dashboard Test Song 1', artist='Artist A'),
                Song(title='Dashboard Test Song 2', artist='Artist B'),
                Song(title='Dashboard Test Song 3', artist='Artist C'),
                Song(title='Dashboard Test Song 4', artist='Artist A'),
                Song(title='Dashboard Test Song 5', artist='Artist D')
            ]
            for song in test_songs:
                db.session.add(song)
                
            db.session.commit()
            
            test_reviews = [
                Review(rating=5, comment="Excellent song!", username='testuser', song_id=1),
                Review(rating=4, comment="Pretty good", username='testuser', song_id=2),
                Review(rating=3, comment="It's okay", username='testuser', song_id=3),
                Review(rating=5, comment="Another great one", username='testuser', song_id=4)
            ]
            for review in test_reviews:
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
    
    def test_dashboard_statistics(self):
        """Test that dashboard displays correct statistics"""
        logger.info("Running test_dashboard_statistics")
        self.login_user()
        
        try:
            self.driver.save_screenshot("dashboard.png")
            
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "stat-card")))
            
            logger.info("Dashboard page content accessible")
            
            self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "stat-value")))
            
            stat_value_elements = self.driver.find_elements(By.CLASS_NAME, "stat-value")
            logger.info(f"Found {len(stat_value_elements)} stat value elements")
            
            assert len(stat_value_elements) >= 3, f"Expected at least 3 statistic values, found {len(stat_value_elements)}"
            
            total_reviews = stat_value_elements[0].text
            reviewed_songs = stat_value_elements[1].text
            reviewed_artists = stat_value_elements[2].text
            
            logger.info(f"Stats found - total reviews: {total_reviews}, reviewed songs: {reviewed_songs}, reviewed artists: {reviewed_artists}")
            
            assert total_reviews == "4", f"Expected 4 total reviews, got {total_reviews}"
            
            assert reviewed_songs == "4", f"Expected 4 reviewed songs, got {reviewed_songs}"
            
            assert reviewed_artists == "3", f"Expected 3 reviewed artists, got {reviewed_artists}"
            
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "activity-feed")))
            activity_feed = self.driver.find_element(By.CLASS_NAME, "activity-feed")
            review_items = activity_feed.find_elements(By.CLASS_NAME, "review-item")
            
            assert len(review_items) > 0, "No review items found in the activity feed"
            
            test_review_found = False
            for item in review_items:
                if "Excellent song!" in item.text:
                    test_review_found = True
                    break
                    
            assert test_review_found, "Test review was not found in the activity feed"
            logger.info("test_dashboard_statistics passed")
            
        except Exception as e:
            self.driver.save_screenshot("dashboard_stats_error.png")
            logger.error(f"Error in test_dashboard_statistics: {str(e)}")
            raise
    
    def test_navigation_links(self):
        """Test that navigation links in the sidebar work correctly"""
        logger.info("Running test_navigation_links")
        self.login_user()
        
        try:
            self.driver.find_element(By.LINK_TEXT, "My Reviews").click()
            self.wait.until(EC.url_contains("my-reviews"))
            assert "My Reviews" in self.driver.title
            
            self.driver.find_element(By.LINK_TEXT, "Search Music").click()
            self.wait.until(EC.url_contains("search"))
            assert "Search Music" in self.driver.title
            
            self.driver.find_element(By.LINK_TEXT, "Shared Reviews").click()
            self.wait.until(EC.url_contains("shared-reviews"))
            
            self.driver.find_element(By.LINK_TEXT, "Dashboard").click()
            self.wait.until(EC.url_contains("dashboard"))
            assert "Dashboard" in self.driver.title
            
            logger.info("test_navigation_links passed")
            
        except Exception as e:
            self.driver.save_screenshot("navigation_error.png")
            logger.error(f"Error in test_navigation_links: {str(e)}")
            raise
    
    def test_combined_workflow(self):
        """Test a combined workflow: search -> add -> review -> view in my reviews"""
        logger.info("Running test_combined_workflow")
        self.login_user()
        
        try:
            self.driver.find_element(By.LINK_TEXT, "Search Music").click()
            self.wait.until(EC.visibility_of_element_located((By.ID, "query")))
            
            search_term = "Unique Workflow Test Song"
            self.driver.find_element(By.ID, "query").send_keys(search_term)
            
            search_button = self.driver.find_element(By.CLASS_NAME, "btn-primary")
            self.driver.execute_script("arguments[0].click();", search_button)
            
            self.wait.until(EC.visibility_of_element_located((By.ID, "artist")))
            self.driver.find_element(By.ID, "artist").send_keys("Workflow Test Artist")
            self.driver.find_element(By.ID, "title").send_keys(search_term)
            
            add_button = self.driver.find_element(By.CLASS_NAME, "btn-success")
            self.driver.execute_script("arguments[0].click();", add_button)
            
            self.wait.until(EC.visibility_of_element_located((By.XPATH, f"//h3[contains(text(), '{search_term}')]")))
            
            self.wait.until(EC.visibility_of_element_located((By.ID, "rating")))
            
            rating_select = Select(self.driver.find_element(By.ID, "rating"))
            rating_select.select_by_visible_text("★★★★★ (5 stars)")
            
            comment_field = self.driver.find_element(By.ID, "comment")
            test_comment = "This is a test of the complete workflow - great song!"
            comment_field.send_keys(test_comment)
            
            submit_button = self.driver.find_element(By.NAME, "submit")
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            self.wait.until(EC.url_contains("my-reviews"))
            
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "review-item")))
            reviews = self.driver.find_elements(By.CLASS_NAME, "review-item")
            
            workflow_review_found = False
            for review in reviews:
                if search_term in review.text and test_comment in review.text:
                    workflow_review_found = True
                    break
                    
            assert workflow_review_found, "Newly created review from workflow was not found"
            
            self.driver.find_element(By.LINK_TEXT, "Dashboard").click()
            self.wait.until(EC.url_contains("dashboard"))
            
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "stat-value")))
            stat_value_elements = self.driver.find_elements(By.CLASS_NAME, "stat-value")
            total_reviews = stat_value_elements[0].text
            assert total_reviews == "5", f"Expected 5 total reviews after workflow, got {total_reviews}"
            
            logger.info("test_combined_workflow passed")
            
        except Exception as e:
            self.driver.save_screenshot("workflow_error.png")
            logger.error(f"Error in test_combined_workflow: {str(e)}")
            raise