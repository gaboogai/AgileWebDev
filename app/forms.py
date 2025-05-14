from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, ValidationError
from app.models import User

class ReviewSendForm(FlaskForm):
    """Form for sending reviews to a recipient"""
    recipient_username = StringField('Recipient Username', validators=[DataRequired(message="Please enter a recipient username.")])
    review = SelectField('Choose a Review', choices = [])
    submit = SubmitField('Send Reviews')