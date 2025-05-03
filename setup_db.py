from app import create_app, db
from app.models import User, Song, Review

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database tables created successfully.")
    
    demo_user = User(username='demo', password='demo123')
    test_user = User(username='test', password='test123')
    db.session.add(demo_user)
    db.session.add(test_user)
    
    songs = [
        Song(title='Bohemian Rhapsody', artist='Queen'),
        Song(title='Imagine', artist='John Lennon'),
        Song(title='Billie Jean', artist='Michael Jackson')
    ]
    for song in songs:
        db.session.add(song)
    
    db.session.commit()
    print("Sample data added successfully.")