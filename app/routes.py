from flask import render_template, redirect, url_for, request, flash, session
from app import app, db
from app.modules import User, Song, Review

@app.route('/')
@app.route('/index')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
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
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('index'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('index'))
        
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
    
    user_reviews = Review.query.filter_by(username=username).all()
    
    total_reviews = len(user_reviews)
    reviewed_songs = db.session.query(Review.song_id).filter_by(username=username).distinct().count()
    reviewed_artists = db.session.query(Song.artist).join(Review).filter(Review.username == username).distinct().count()
    
    recent_reviews = Review.query.filter_by(username=username).order_by(Review.id.desc()).limit(5).all()
    
    top_albums = db.session.query(Song).join(Review).group_by(Song.id).order_by(db.func.avg(Review.rating).desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           title="Dashboard",
                           user=user,
                           total_reviews=total_reviews,
                           reviewed_songs=reviewed_songs,
                           reviewed_artists=reviewed_artists,
                           recent_reviews=recent_reviews,
                           top_albums=top_albums)

@app.route('/add-review', methods=['POST'])
def add_review():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    artist = request.form['artist']
    title = request.form['title']
    rating = int(request.form['rating'])
    review_text = request.form['review']
    username = session['username']
    
    song = Song.query.filter_by(title=title, artist=artist).first()
    
    if not song:
        song = Song(title=title, artist=artist)
        db.session.add(song)
        db.session.commit()

    new_review = Review(rating=rating, comment=review_text, username=username, song_id=song.id)
    db.session.add(new_review)
    db.session.commit()
    
    flash('Review added successfully!')
    return redirect(url_for('dashboard'))

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
        results = Song.query.filter(
            (Song.title.ilike(f'%{query}%')) | (Song.artist.ilike(f'%{query}%'))
        ).all()
    
    return render_template('search.html', title="Search Music", results=results, query=query)