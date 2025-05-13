from flask import render_template, redirect, url_for, request, flash
from flask_login import UserMixin
from app import app, db
from app.models import User, Song, Review, ReviewShares
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm

@app.route('/')
@app.route('/index')
def index():
    return render_template("login.html", title="Welcome to TUN'D")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
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
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    username = current_user.get_id()
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
    top_songs = db.session.query(Song).join(Review).group_by(Song.id).order_by(db.func.avg(Review.rating).desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           title="Dashboard",
                           user=user,
                           total_reviews=total_reviews,
                           reviewed_songs=reviewed_songs,
                           reviewed_artists=reviewed_artists,
                           recent_reviews=recent_reviews,
                           top_songs=top_songs)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/my-reviews')
@login_required
def my_reviews():
    username = current_user.get_id()
    user_reviews = Review.query.filter_by(username=username).order_by(Review.id.desc()).all()
    
    return render_template('my_reviews.html', title="My Reviews", reviews=user_reviews)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    results = []
    
    if query:
        # Search for songs by title or artist
        results = Song.query.filter(
            (Song.title.ilike(f'%{query}%')) | (Song.artist.ilike(f'%{query}%'))
        ).all()
    
    return render_template('search.html', title="Search Music", results=results, query=query)

@app.route('/add-song', methods=['POST'])
@login_required
def add_song():
    
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
@login_required
def review(song_id):
    
    song = Song.query.get_or_404(song_id)
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        username = current_user.get_id()
        
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
    
    return render_template('review.html', title=f"Review - {song.title}", song=song, existing_review=existing_review)

@app.route('/share')
@login_required
def share_review():
    
    username = current_user.get_id()
    user = User.query.filter_by(username=username).first()
    
    # Get recent reviews
    reviews = Review.query.filter_by(username=username).order_by(Review.id.desc()).all()
    
    
    return render_template("share.html", title="Share", 
                           user=user,
                           reviews=reviews,)


@app.route('/prepare-share', methods=['POST'])
@login_required
def prepare_share():
    
    # Get selected review IDs from form
    selected_review_ids = request.form.getlist('selected_reviews')
    
    if not selected_review_ids:
        flash('Please select at least one review to share.')
        return redirect(url_for('share_review'))
    
    # Get full review objects for the selected IDs
    reviews = []
    for review_id in selected_review_ids:
        review = Review.query.get(int(review_id))
        if review and review.username == current_user.get_id():
            reviews.append(review)
    
    if not reviews:
        flash('No valid reviews were selected.')
        return redirect(url_for('share_review'))
    
    return render_template('send.html', 
                           title="Send Reviews", 
                           selected_reviews=selected_review_ids,
                           reviews=reviews,
                           form=FlaskForm())

@app.route('/share-reviews', methods=['POST'])
@login_required
def share_reviews():
    review_ids = request.form.getlist('review_ids')
    recipient_username = request.form.get('recipient_username')

    form = FlaskForm()
    if not form.validate_on_submit():
        flash('Invalid form submission. Please try again.')
        return redirect(url_for('share_review'))
    
    if not review_ids or not recipient_username:
        flash('Missing information. Please try again.')
        return redirect(url_for('share_review'))
    
    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        flash(f'User "{recipient_username}" does not exist.')
        return redirect(url_for('prepare_share'))
    
    for review_id in review_ids:
        review = Review.query.get(int(review_id))
        if review and review.username == current_user.get_id():
            existing_share = ReviewShares.query.filter_by(review_id=review.id, username=recipient_username).first()
            
            if not existing_share:
                new_share = ReviewShares(review_id=review.id, username=recipient_username)
                db.session.add(new_share)
    
    db.session.commit()
    flash('Reviews shared successfully!')
    return redirect(url_for('share_review'))


@app.route('/shared-reviews')
@login_required
def shared_reviews():
    username = current_user.get_id()
    
    shared_reviews = db.session.query(Review).\
        join(ReviewShares, Review.id == ReviewShares.review_id).\
        filter(ReviewShares.username == username).all()
    
    for review in shared_reviews:
        review.song_details = Song.query.get(review.song_id)
    
    return render_template('shared_reviews.html', 
                           title="Reviews Shared With Me", 
                           shared_reviews=shared_reviews)

