from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, RadioField
from wtforms.validators import DataRequired, Length, URL, Optional, ValidationError
import re

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
