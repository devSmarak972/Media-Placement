"""
Media Placements Tracker - Application Launcher

This script sets up and runs the Media Placements Tracker application.
It initializes the SQLite database, creates tables if they don't exist,
and starts the Flask application server.
"""

import os
import sys
import logging
from app import app, db
from models import MediaPlacement, GoogleCredential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('MediaPlacementsApp')

def initialize_database():
    """
    Initialize the SQLite database and create tables if they don't exist.
    """
    try:
        # Create all tables
        with app.app_context():
            # Handle SQLite file path if using SQLite
            if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
                db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                if db_file and not db_file.startswith(':memory:'):
                    # Create directory for SQLite file if needed
                    db_dir = os.path.dirname(db_file)
                    if db_dir and not os.path.exists(db_dir):
                        os.makedirs(db_dir)
                        logger.info(f"Created directory for SQLite database: {db_dir}")
            
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False

def run_application():
    """
    Start the Flask application server.
    """
    try:
        # Initialize database
        if not initialize_database():
            logger.error("Failed to initialize database. Exiting.")
            return
        
        # Set host to 0.0.0.0 to make the app accessible externally
        host = os.environ.get('HOST', '0.0.0.0')
        
        # Use the specified port or default to 5000
        port = int(os.environ.get('PORT', 5000))
        
        # Determine if debug mode should be enabled
        debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
        
        # Start the Flask app
        logger.info(f"Starting Media Placements Tracker on {host}:{port} (Debug: {debug})")
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"Application startup error: {str(e)}")

if __name__ == '__main__':
    run_application()
