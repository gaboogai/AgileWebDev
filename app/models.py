from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from app import app, db, login
from flask_login import UserMixin

# Set up base directory and database config
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'app', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# User model for authentication and user data
class User(db.Model, UserMixin):
    username = db.Column(db.String(20), primary_key=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    reviews = db.relationship('Review', backref='reviewer', lazy='dynamic')
    
    def get_id(self):
        return self.username

# Song model for storing song info
class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    reviews = db.relationship('Review', backref='song', lazy='dynamic')

# Review model for storing reviews
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)

# ReviewShares model for sharing reviews with users
class ReviewShares(db.Model):
    share_id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id', name="required"), nullable=False)
    username = db.Column(db.String(20), db.ForeignKey('user.username', name="required2"), nullable=False)

# User loader callback for Flask-Login
@login.user_loader
def load_user(user):
    return User.query.filter_by(username=user).first()
