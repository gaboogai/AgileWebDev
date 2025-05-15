import pytest
import os
import tempfile
from app import app, db
from app.models import User, Song, Review
from werkzeug.security import generate_password_hash

@pytest.fixture(scope='session')
def flask_app():
    """Create and configure a Flask app for testing."""
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test_secret'
    })
    
    db_fd, db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    with app.app_context():
        db.create_all()
        
        seed_test_data()
        
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='session')
def client(flask_app):
    """A test client for the app."""
    return flask_app.test_client()

@pytest.fixture(scope='session')
def runner(flask_app):
    """A CLI runner for the app."""
    return flask_app.test_cli_runner()

def seed_test_data():
    """Add initial test data to the database."""
    test_user = User(username='testuser', password=generate_password_hash('testpassword'))
    admin_user = User(username='admin', password=generate_password_hash('adminpassword'))
    
    db.session.add(test_user)
    db.session.add(admin_user)
    
    songs = [
        Song(title='Test Song 1', artist='Test Artist 1'),
        Song(title='Test Song 2', artist='Test Artist 2'),
        Song(title='Test Song 3', artist='Test Artist 3')
    ]
    
    for song in songs:
        db.session.add(song)
    
    db.session.commit()
    
    reviews = [
        Review(rating=5, comment='Great song!', username='testuser', song_id=1),
        Review(rating=3, comment='It\'s okay.', username='testuser', song_id=2),
        Review(rating=4, comment='Pretty good.', username='admin', song_id=1)
    ]
    
    for review in reviews:
        db.session.add(review)
    
    db.session.commit()