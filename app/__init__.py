from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from flask_login import LoginManager

# Initialize Flask app
app = Flask(__name__)

# Set up base and parent directories
basedir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(basedir)
# Configure SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
# Set secret key from environment variable
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
# Disable SQLAlchemy event system
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and migration
db = SQLAlchemy(app)
migrate = Migrate(app,db,render_as_batch=True)
# Set up login manager
login = LoginManager(app)
login.login_view = 'index'

from app import routes, models  # Import routes and models

# Register CLI commands
from app.commands import init_db_command, seed_db_command
app.cli.add_command(init_db_command)
app.cli.add_command(seed_db_command)