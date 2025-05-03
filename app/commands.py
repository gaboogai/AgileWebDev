import click
from flask.cli import with_appcontext
from app import db
from app.modules import User, Song, Review

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database."""
    db.create_all()
    click.echo('Initialized the database.')

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Seed the database with sample data."""
    users = [
        User(username='demo', password='demo123'),
        User(username='test', password='test123')
    ]
    
    songs = [
        Song(title='Bohemian Rhapsody', artist='Queen'),
        Song(title='Imagine', artist='John Lennon'),
        Song(title='Billie Jean', artist='Michael Jackson'),
        Song(title='Hey Jude', artist='The Beatles'),
        Song(title='Smells Like Teen Spirit', artist='Nirvana')
    ]
    
    for user in users:
        db.session.add(user)
    
    for song in songs:
        db.session.add(song)
    
    db.session.commit()
    
    reviews = [
        Review(rating=5, comment='A masterpiece!', username='demo', song_id=1),
        Review(rating=4, comment='Classic song', username='demo', song_id=2),
        Review(rating=5, comment='One of the best songs ever', username='test', song_id=1),
        Review(rating=3, comment='Good, but not my favorite', username='test', song_id=3)
    ]
    
    for review in reviews:
        db.session.add(review)
    
    db.session.commit()
    click.echo('Database seeded with sample data.')