import os

base_dir = os.path.abspath(os.path.dirname(__file__))
default_database_location =  'sqlite:///' + os.path.join(base_dir, 'app.db')

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or default_database_location
    SECRET_KEY = "you-will-never-guess"
    SQLALCHEMY_TRACK_MODIFICATIONS = False