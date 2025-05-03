from flask import render_template, redirect, url_for, request, flash, session
from app import app, db
from app.models import User, Song, Review

@app.route('/')
@app.route('/index')
def index():
    # If user is logged in, redirect to dashboard
    if 'username' in session:
        return redirect(url_for('dashboard'))
    # Otherwise show the login/register page
    return render_template("login.html", title="Welcome to TUN'D")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['new_username']
        password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('index'))
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('index'))
        
        # Create new user
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        session['username'] = username
        return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    
    # Get user's reviews
    user_reviews = Review.query.filter_by(username=username).all()
    
    # Count statistics
    total_reviews = len(user_reviews)
    reviewed_songs = db.session.query(Review.song_id).filter_by(username=username).distinct().count()
    reviewed_artists = db.session.query(Song.artist).join(Review).filter(Review.username == username).distinct().count()
    
    # Get recent reviews
    recent_reviews = Review.query.filter_by(username=username).order_by(Review.id.desc()).limit(5).all()
    
    # Get top rated albums and songs
    top_albums = db.session.query(Song).join(Review).group_by(Song.id).order_by(db.func.avg(Review.rating).desc()).limit(5).all()
    top_songs = top_albums  # Use the same list for both since we only track songs
    
    return render_template('dashboard.html', 
                           title="Dashboard",
                           user=user,
                           total_reviews=total_reviews,
                           reviewed_songs=reviewed_songs,
                           reviewed_artists=reviewed_artists,
                           recent_reviews=recent_reviews,
                           top_albums=top_albums,
                           top_songs=top_songs)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/my-reviews')
def my_reviews():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    username = session['username']
    user_reviews = Review.query.filter_by(username=username).order_by(Review.id.desc()).all()
    
    return render_template('my_reviews.html', title="My Reviews", reviews=user_reviews)

@app.route('/search')
def search():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    query = request.args.get('q', '')
    results = []
    
    if query:
        # Search for songs by title or artist
        results = Song.query.filter(
            (Song.title.ilike(f'%{query}%')) | (Song.artist.ilike(f'%{query}%'))
        ).all()
    
    return render_template('search.html', title="Search Music", results=results, query=query)

@app.route('/add-song', methods=['POST'])
def add_song():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    artist = request.form['artist']
    title = request.form['title']
    
    # Check if song exists
    existing_song = Song.query.filter_by(title=title, artist=artist).first()
    
    if existing_song:
        flash('This song already exists')
        return redirect(url_for('search', q=artist))
    
    # Create new song
    new_song = Song(title=title, artist=artist)
    db.session.add(new_song)
    db.session.commit()
    
    flash('Song added successfully! Now you can review it.')
    return redirect(url_for('review', song_id=new_song.id))

@app.route('/review/<int:song_id>', methods=['GET', 'POST'])
def review(song_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    
    song = Song.query.get_or_404(song_id)
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        username = session['username']
        
        # Check if user already reviewed this song
        existing_review = Review.query.filter_by(username=username, song_id=song_id).first()
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.comment = comment
            db.session.commit()
            flash('Your review has been updated!')
        else:
            # Create new review
            new_review = Review(rating=rating, comment=comment, username=username, song_id=song_id)
            db.session.add(new_review)
            db.session.commit()
            flash('Your review has been added!')
        
        return redirect(url_for('my_reviews'))
    
    # Check if user has already reviewed this song
    existing_review = None
    if 'username' in session:
        existing_review = Review.query.filter_by(username=session['username'], song_id=song_id).first()
    
    return render_template('review.html', title=f"Review - {song.title}", song=song, existing_review=existing_review)

# Keep these legacy routes for backward compatibility
@app.route('/button')
def button():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template("button.html", title="Button!")

@app.route('/share')
def share():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template("share.html", title="Share")