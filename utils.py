import os
import logging
from logging.handlers import RotatingFileHandler
import re
from datetime import datetime
from urllib.parse import urlparse

def setup_logging(app):
    """Configure logging for the application."""
    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Media Placements App startup')

def clean_url(url):
    """Normalize and clean URLs for consistent comparison."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed = urlparse(url)
    cleaned_url = f"{parsed.netloc}{parsed.path}"
    cleaned_url = cleaned_url.rstrip('/')
    cleaned_url = cleaned_url.lower()
    
    return cleaned_url

def get_domain_from_url(url):
    """Extract domain from URL."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Remove www. prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain

def is_valid_date_string(date_str):
    """Validate if a string is a valid date in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def format_date_for_display(date_obj):
    """Format a date object for display in the UI."""
    if not date_obj:
        return ''
    
    return date_obj.strftime('%B %d, %Y')

def truncate_text(text, max_length=100):
    """Truncate text to a specified length and add ellipsis if needed."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + '...'
