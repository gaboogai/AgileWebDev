from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'app', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    username = db.Column(db.String(20), primary_key=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    reviews = db.relationship('Review', backref='reviewer', lazy='dynamic')

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    reviews = db.relationship('Review', backref='song', lazy='dynamic')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)

with app.app_context():
    os.makedirs(os.path.join(base_dir, 'app'), exist_ok=True)
    
    db.drop_all()
    db.create_all()
    print("Database tables created.")
    
    sample_users = [
        User(username='demo', password='demo123'),
        User(username='test', password='test123')
    ]
    
    for user in sample_users:
        db.session.add(user)
    
    sample_songs = [
        Song(title='Bohemian Rhapsody', artist='Queen'),
        Song(title='Imagine', artist='John Lennon'),
        Song(title='Billie Jean', artist='Michael Jackson'),
        Song(title='Hey Jude', artist='The Beatles'),
        Song(title='Smells Like Teen Spirit', artist='Nirvana')
    ]
    
    for song in sample_songs:
        db.session.add(song)
    
    db.session.commit()
    
    sample_reviews = [
        Review(rating=5, comment='A masterpiece!', username='demo', song_id=1),
        Review(rating=4, comment='Classic song', username='demo', song_id=2),
        Review(rating=5, comment='One of the best songs ever', username='test', song_id=1),
        Review(rating=3, comment='Good, but not my favorite', username='test', song_id=3)
    ]
    
    for review in sample_reviews:
        db.session.add(review)
    
    db.session.commit()
    
    print("Sample data added successfully.")