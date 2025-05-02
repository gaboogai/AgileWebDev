from app import db
from datetime import datetime

class User(db.Model):
    username = db.Column(db.String(20), primary_key=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    reviews = db.relationship('Review', backref='reviewer', lazy='dynamic')
    shared_from = db.relationship('SharedSong', backref='sender', foreign_keys='SharedSong.sender_username', lazy='dynamic')
    shared_to = db.relationship('SharedSong', backref='recipient', foreign_keys='SharedSong.recipient_username', lazy='dynamic')

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    youtube_link = db.Column(db.String(200))
    reviews = db.relationship('Review', backref='song', lazy='dynamic')
    shares = db.relationship('SharedSong', backref='song', lazy='dynamic')
    
    __table_args__ = (db.UniqueConstraint('title', 'artist', name='_title_artist_uc'),)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('username', 'song_id', name='_user_song_uc'),)

class SharedSong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
    recipient_username = db.Column(db.String(20), db.ForeignKey('user.username'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    date_shared = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)