from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class MediaPlacement(db.Model):
    __tablename__ = 'media_placements'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), nullable=False)
    title = db.Column(db.String(256), nullable=True)
    source = db.Column(db.String(128), nullable=True)
    publication_date = db.Column(db.Date, nullable=True)
    media_type = db.Column(db.String(64), default='article')  # article, video, podcast, etc.
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)  # Allow NULL for user_id now that we don't use authentication
    docket_url = db.Column(db.String(512), nullable=True)  # URL to the Google Doc docket
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MediaPlacement {self.title}>'

class GoogleCredential(db.Model):
    __tablename__ = 'google_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(256), nullable=True)
    oauth_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.String(256), nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)  # Make user_id nullable
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<GoogleCredential {self.id}>'
