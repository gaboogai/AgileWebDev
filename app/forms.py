from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, ValidationError, EqualTo
from app.models import User

# Login form for users
class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired(message="Please enter your username.")])
    password = PasswordField('Password', validators=[DataRequired(message="Please enter your password.")])
    submit = SubmitField('Login')

# Registration form for new users
class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[DataRequired(message="Please choose a username.")])
    password = PasswordField('Password', validators=[DataRequired(message="Please choose a password.")])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(message="Please confirm your password."),
                                               EqualTo('password', message="Passwords must match.")])
    submit = SubmitField('Create Account')
    
    # Validate that username is unique
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

# Form to send reviews to another user
class ReviewSendForm(FlaskForm):
    """Form for sending reviews to a recipient"""
    recipient_username = StringField('Recipient Username', validators=[DataRequired(message="Please enter a recipient username.")])
    review = SelectField('Choose a Review', choices = [])
    submit = SubmitField('Send Reviews')

# Form for searching songs or artists
class SearchForm(FlaskForm):
    """Form for searching songs and artists"""
    query = StringField('Search', validators=[DataRequired(message="Please enter a search term.")])
    submit = SubmitField('Search')

# Form for adding a new song
class AddSongForm(FlaskForm):
    """Form for adding a new song"""
    artist = StringField('Artist', validators=[DataRequired(message="Please enter the artist name.")])
    title = StringField('Song Title', validators=[DataRequired(message="Please enter the song title.")])
    submit = SubmitField('Add Song')

# Form for submitting a review for a song
class ReviewForm(FlaskForm):
    """Form for submitting song reviews"""
    rating = SelectField('Your Rating (1-5 stars)', 
                        choices=[
                            ('5', '★★★★★ (5 stars)'),
                            ('4', '★★★★☆ (4 stars)'),
                            ('3', '★★★☆☆ (3 stars)'),
                            ('2', '★★☆☆☆ (2 stars)'),
                            ('1', '★☆☆☆☆ (1 star)')
                        ],
                        validators=[DataRequired(message="Please select a rating.")])
    comment = StringField('Your Comments (optional)')
    submit = SubmitField('Submit Review')