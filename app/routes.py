from flask import render_template
from app import app
@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Miguel'}
    posts = [
    {
    'author': {'username': 'John'},
    'body': 'Beautiful day in Portland!'
    },
    {
    'author': {'username': 'Susan'},
    'body': 'The Avengers movie was so cool!'
    }
    ]
    return render_template("index.html", title="Home", user=user, posts=posts)

@app.route('/button')
def button():
    return render_template("button.html", title="Button!")

@app.route('/share')
def share():
    return render_template("share.html", title="Share")

@app.route('/add-song', methods=['POST'])
def add_song():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    artist = request.form['artist']
    title = request.form['title']
    
    existing_song = Song.query.filter_by(title=title, artist=artist).first()
    
    if existing_song:
        flash('This song already exists')
        return redirect(url_for('search', q=artist))
    
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
        
        existing_review = Review.query.filter_by(username=username, song_id=song_id).first()
        
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
    
    existing_review = None
    if 'username' in session:
        existing_review = Review.query.filter_by(username=session['username'], song_id=song_id).first()
    
    return render_template('review.html', title=f"Review - {song.title}", song=song, existing_review=existing_review)