from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    placements = db.relationship('MediaPlacement', backref='user', lazy='dynamic')
    google_credential = db.relationship('GoogleCredential', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class MediaPlacement(db.Model):
    __tablename__ = 'media_placements'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), nullable=False)
    title = db.Column(db.String(256), nullable=True)
    source = db.Column(db.String(128), nullable=True)
    publication_date = db.Column(db.Date, nullable=True)
    media_type = db.Column(db.String(64), default='article')  # article, video, podcast, etc.
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<MediaPlacement {self.title}>'

class GoogleCredential(db.Model):
    __tablename__ = 'google_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    api_key = db.Column(db.String(256), nullable=True)
    oauth_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.String(256), nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<GoogleCredential for User {self.user_id}>'
