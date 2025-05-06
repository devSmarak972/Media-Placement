from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, RadioField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, URL, Optional, ValidationError
import re

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        'Confirm Password', 
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')]
    )
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        from models import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        from models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one or login.')

class AddPlacementForm(FlaskForm):
    input_type = RadioField(
        'Input Method', 
        choices=[
            ('direct', 'Direct Text Input'),
            ('gdoc', 'Google Doc'),
            ('gsheet', 'Google Sheet')
        ],
        default='direct'
    )
    
    text_input = TextAreaField('Paste URLs or text containing URLs')
    google_doc_id = StringField('Google Doc ID or URL')
    google_sheet_id = StringField('Google Sheet ID or URL')
    
    submit = SubmitField('Extract & Add Media Placements')
    
    def validate_google_doc_id(self, field):
        if self.input_type.data == 'gdoc' and not field.data:
            raise ValidationError('Please provide a Google Doc ID or URL.')
        
        # Extract doc ID from URL if full URL is provided
        if field.data and 'docs.google.com' in field.data:
            match = re.search(r'/d/([a-zA-Z0-9-_]+)', field.data)
            if match:
                field.data = match.group(1)
    
    def validate_google_sheet_id(self, field):
        if self.input_type.data == 'gsheet' and not field.data:
            raise ValidationError('Please provide a Google Sheet ID or URL.')
        
        # Extract sheet ID from URL if full URL is provided
        if field.data and 'spreadsheets' in field.data:
            match = re.search(r'/d/([a-zA-Z0-9-_]+)', field.data)
            if match:
                field.data = match.group(1)

class GoogleCredentialForm(FlaskForm):
    api_key = StringField('Google API Key', validators=[DataRequired()])
    submit = SubmitField('Save API Key')

class EditPlacementForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired(), URL()])
    title = StringField('Title', validators=[Optional(), Length(max=256)])
    source = StringField('Source', validators=[Optional(), Length(max=128)])
    publication_date = StringField('Publication Date (YYYY-MM-DD)', validators=[Optional()])
    media_type = SelectField(
        'Media Type',
        choices=[
            ('article', 'Article'),
            ('video', 'Video'),
            ('podcast', 'Podcast'),
            ('blog', 'Blog Post'),
            ('social', 'Social Media'),
            ('press_release', 'Press Release'),
            ('other', 'Other')
        ]
    )
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Update Placement')
