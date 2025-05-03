from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models

from app.models import User, Song, Review

from app.commands import init_db_command, seed_db_command
app.cli.add_command(init_db_command)
app.cli.add_command(seed_db_command)