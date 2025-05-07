import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Database configuration - using SQLite by default for persistence and portability
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///media_placements.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Google API configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')
    
    # Determine the correct redirect URI based on the environment
    if os.environ.get('REPLIT_DEV_DOMAIN'):
        redirect_uri = f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}/google/auth/callback"
    else:
        redirect_uri = 'http://localhost:5000/google/auth/callback'
        
    # Print the configured redirect URL to make it clear for Google OAuth setup
    print(f"Google OAuth Redirect URI: {redirect_uri}")
    print("Please make sure to add this URI to your Google OAuth Consent Screen configuration!")
    
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', redirect_uri)
    
    # Expanded scopes to allow write operations for docs and sheets
    GOOGLE_AUTH_SCOPES = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]
