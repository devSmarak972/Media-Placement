import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://{}:{}@{}:{}/{}'.format(
        os.environ.get('PGUSER', 'postgres'),
        os.environ.get('PGPASSWORD', 'postgres'),
        os.environ.get('PGHOST', 'localhost'),
        os.environ.get('PGPORT', '5432'),
        os.environ.get('PGDATABASE', 'mediaplacements')
    ))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Google API configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/google/auth/callback')
    GOOGLE_AUTH_SCOPES = [
        'https://www.googleapis.com/auth/documents.readonly',
        'https://www.googleapis.com/auth/spreadsheets.readonly'
    ]
