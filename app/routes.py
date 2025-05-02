from flask import render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from app.modules import User, Song, Review, SharedSong
from datetime import datetime
import json

@app.route('/')
@app.route('/index')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template("intro.html", title="TUN'D - Music Rating Platform")

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['new_username']
        password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('index'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('index'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out!', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('index'))
        
    username = session['username']
    user = User.query.filter_by(username=username).first()
    
    total_reviews = Review.query.filter_by(username=username).count()
    reviewed_songs = db.session.query(Song).join(Review).filter(Review.username == username).distinct().count()
    reviewed_artists = db.session.query(Song.artist).join(Review).filter(Review.username == username).distinct().count()
    
    recent_reviews = db.session.query(Review, Song).join(Song).filter(Review.username == username).order_by(Review.date_posted.desc()).limit(5).all()
    
    top_songs = db.session.query(
        Song,
        db.func.avg(Review.rating).label('avg_rating')
    ).join(Review).group_by(Song.id).order_by(db.desc('avg_rating')).limit(5).all()
    
    top_albums = top_songs
    
    return render_template(
        "dashboard.html", 
        title="Dashboard", 
        user=user,
        total_reviews=total_reviews,
        reviewed_songs=reviewed_songs,
        reviewed_artists=reviewed_artists,
        recent_reviews=recent_reviews,
        top_songs=top_songs,
        top_albums=top_albums
    )

@app.route('/add-review', methods=['POST'])
def add_review():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = session['username']
        artist = request.form['artist']
        title = request.form['title']
        rating = int(request.form['rating'])
        review_text = request.form.get('review', '')
        
        song = Song.query.filter_by(title=title, artist=artist).first()
        if not song:
            song = Song(title=title, artist=artist)
            db.session.add(song)
            db.session.commit()
            
        existing_review = Review.query.filter_by(username=username, song_id=song.id).first()
        if existing_review:
            existing_review.rating = rating
            existing_review.comment = review_text
            existing_review.date_posted = datetime.utcnow()
        else:
            new_review = Review(
                rating=rating,
                comment=review_text,
                username=username,
                song_id=song.id
            )
            db.session.add(new_review)
            
        db.session.commit()
        flash('Review added successfully!', 'success')
        return redirect(url_for('dashboard'))

@app.route('/my-reviews')
def my_reviews():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('index'))
        
    username = session['username']
    reviews = db.session.query(Review, Song).join(Song).filter(Review.username == username).order_by(Review.date_posted.desc()).all()
    
    return render_template("my_reviews.html", title="My Reviews", reviews=reviews)

@app.route('/search')
def search():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('index'))
        
    query = request.args.get('q', '')
    results = []
    
    if query:
        results = Song.query.filter(
            (Song.title.like(f'%{query}%')) | 
            (Song.artist.like(f'%{query}%'))
        ).all()
        
    return render_template("search.html", title="Search Music", query=query, results=results)

@app.route('/share', methods=['GET', 'POST'])
def share():
    if 'username' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('index'))
        
    username = session['username']
    users = User.query.filter(User.username != username).all()
    
    if request.method == 'POST':
        song_name = request.form.get('songName')
        artist = request.form.get('artist')
        youtube_link = request.form.get('youtubeLink', '')
        recipient = request.form.get('shareWith')
        
        recipient_user = User.query.filter_by(username=recipient).first()
        if not recipient_user:
            flash('Selected user does not exist!', 'danger')
            return redirect(url_for('share'))
            
        song = Song.query.filter_by(title=song_name, artist=artist).first()
        if not song:
            song = Song(title=song_name, artist=artist, youtube_link=youtube_link)
            db.session.add(song)
            db.session.commit()
            
        new_share = SharedSong(
            sender_username=username,
            recipient_username=recipient,
            song_id=song.id
        )
        
        db.session.add(new_share)
        db.session.commit()
        
        flash('Song shared successfully!', 'success')
        return redirect(url_for('share'))
        
    shared_songs = db.session.query(
        SharedSong, Song, User
    ).join(Song).join(User, SharedSong.sender_username == User.username).filter(
        (SharedSong.sender_username == username) | 
        (SharedSong.recipient_username == username)
    ).order_by(SharedSong.date_shared.desc()).all()
    
    return render_template("share.html", title="Share Music", users=users, shared_songs=shared_songs)