from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from app import app, db, login
from flask_login import UserMixin

base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'app', 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

class User(db.Model, UserMixin):
    username = db.Column(db.String(20), primary_key=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    reviews = db.relationship('Review', backref='reviewer', lazy='dynamic')
    
    def get_id(self):
        return self.username

        

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

class ReviewShares(db.Model):
    share_id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)

@login.user_loader
def load_user(user):
    return User.query.filter_by(username=user).first()
