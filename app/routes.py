from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import UserMixin
from app import app, db
from app.models import User, Song, Review, ReviewShares
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from app.forms import ReviewSendForm, LoginForm, RegistrationForm, SearchForm, AddSongForm, ReviewForm
import datetime

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    register_form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    
    return render_template("login.html", title="Welcome to TUN'D", form=form, register_form=register_form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('Account created successfully!')
        return redirect(url_for('dashboard'))
    
    login_form = LoginForm()
    return render_template('login.html', title="Welcome to TUN'D", form=login_form, register_form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    username = current_user.get_id()
    user = User.query.filter_by(username=username).first()
    
    user_reviews = Review.query.filter_by(username=username).all()
    
    total_reviews = len(user_reviews)
    reviewed_songs = db.session.query(Review.song_id).filter_by(username=username).distinct().count()
    reviewed_artists = db.session.query(Song.artist).join(Review).filter(Review.username == username).distinct().count()
    
    recent_reviews = Review.query.filter_by(username=username).order_by(Review.id.desc()).limit(5).all()
    
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

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    search_form = SearchForm()
    add_song_form = AddSongForm()
    
    if search_form.validate_on_submit():
        return redirect(url_for('search', q=search_form.query.data))
    
    query = request.args.get('q', '')
    if query:
        search_form.query.data = query
        
        results = Song.query.filter(
            (Song.title.ilike(f'%{query}%')) | (Song.artist.ilike(f'%{query}%'))
        ).all()
    else:
        results = []
    
    return render_template('search.html', 
                          title="Search Music", 
                          search_form=search_form, 
                          add_song_form=add_song_form,
                          results=results, 
                          query=query)

@app.route('/add-song', methods=['POST'])
@login_required
def add_song():
    add_song_form = AddSongForm()
    
    if add_song_form.validate_on_submit():
        artist = add_song_form.artist.data
        title = add_song_form.title.data
        
        existing_song = Song.query.filter_by(title=title, artist=artist).first()
        
        if existing_song:
            flash('This song already exists')
            return redirect(url_for('search', q=artist))
        
        new_song = Song(title=title, artist=artist)
        db.session.add(new_song)
        db.session.commit()
        
        flash('Song added successfully! Now you can review it.')
        return redirect(url_for('review', song_id=new_song.id))
    
    flash('Please fill in all the required fields')
    return redirect(url_for('search'))

@app.route('/review/<int:song_id>', methods=['GET', 'POST'])
@login_required
def review(song_id):
    song = Song.query.get_or_404(song_id)
    form = ReviewForm()
    
    existing_review = Review.query.filter_by(username=current_user.get_id(), song_id=song_id).first()
    
    if existing_review and request.method == 'GET':
        form.rating.data = str(existing_review.rating)
        form.comment.data = existing_review.comment
        form.submit.label.text = 'Update Review'
    
    if form.validate_on_submit():
        rating = int(form.rating.data)
        comment = form.comment.data
        username = current_user.get_id()
        
        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            db.session.commit()
            flash('Your review has been updated!')
        else:
            new_review = Review(rating=rating, comment=comment, username=username, song_id=song_id)
            db.session.add(new_review)
            db.session.commit()
            flash('Your review has been added!')
        
        return redirect(url_for('my_reviews'))
    
    return render_template('review.html', title=f"Review - {song.title}", song=song, form=form)

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


@app.route('/current-time')
def current_time():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'time': now})
  

@app.route('/share', methods=['GET', 'POST'])
@login_required
def share():
    username = current_user.get_id()
    user = User.query.filter_by(username=username).first()
    
    reviews = Review.query.filter_by(username=username).order_by(Review.id.desc()).all()

    form = ReviewSendForm()
    
    if reviews:
        form.review.choices = [(str(review.id), f"{review.song.title} - {review.rating}★") for review in reviews]
    else:
        form.review.choices = []

    if form.validate_on_submit():
        try:
            review_id = int(form.review.data)
            new_share = ReviewShares(review_id=review_id, username=form.recipient_username.data)
            db.session.add(new_share)
            db.session.commit()
            flash('Review shared successfully!')
        except Exception as e:
            flash(f'Error sharing review: {str(e)}')
        return redirect(url_for('share'))
    
    return render_template("share.html", title="Share", 
                           user=user,
                           reviews=reviews,
                           form=form)