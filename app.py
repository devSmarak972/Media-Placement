import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import logging

from config import Config
from models import db, User, MediaPlacement, GoogleCredential
from forms import LoginForm, RegistrationForm, AddPlacementForm, GoogleCredentialForm
from auth import auth_bp
from utils import setup_logging
from google_integration import google_bp, get_google_docs_content, get_google_sheets_content
from parsers import extract_links, parse_media_links

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Setup logging
setup_logging(app)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# Setup login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(google_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    placements = MediaPlacement.query.filter_by(user_id=current_user.id).order_by(MediaPlacement.created_at.desc()).all()
    return render_template('dashboard.html', placements=placements)

@app.route('/add_placement', methods=['GET', 'POST'])
@login_required
def add_placement():
    form = AddPlacementForm()
    if form.validate_on_submit():
        # Handle direct text input
        if form.input_type.data == 'direct':
            text_content = form.text_input.data
            links = extract_links(text_content)
            if not links:
                flash('No valid media links found in the provided text.', 'warning')
                return render_template('add_placement.html', form=form)
                
            # Parse and save links
            added_count = 0
            for link in links:
                placement_data = parse_media_links(link)
                if placement_data:
                    placement = MediaPlacement(
                        url=link,
                        title=placement_data.get('title', ''),
                        source=placement_data.get('source', ''),
                        publication_date=placement_data.get('date'),
                        media_type=placement_data.get('type', 'article'),
                        user_id=current_user.id
                    )
                    db.session.add(placement)
                    added_count += 1
            
            if added_count > 0:
                db.session.commit()
                flash(f'Successfully added {added_count} media placements!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Could not extract media information from the provided links.', 'warning')
        
        # Handle Google Docs
        elif form.input_type.data == 'gdoc':
            doc_id = form.google_doc_id.data
            try:
                content = get_google_docs_content(current_user.id, doc_id)
                links = extract_links(content)
                
                if not links:
                    flash('No valid media links found in the Google Doc.', 'warning')
                    return render_template('add_placement.html', form=form)
                
                # Parse and save links (same as above)
                added_count = 0
                for link in links:
                    placement_data = parse_media_links(link)
                    if placement_data:
                        placement = MediaPlacement(
                            url=link,
                            title=placement_data.get('title', ''),
                            source=placement_data.get('source', ''),
                            publication_date=placement_data.get('date'),
                            media_type=placement_data.get('type', 'article'),
                            user_id=current_user.id
                        )
                        db.session.add(placement)
                        added_count += 1
                
                if added_count > 0:
                    db.session.commit()
                    flash(f'Successfully added {added_count} media placements from Google Doc!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Could not extract media information from the links in the Google Doc.', 'warning')
            except Exception as e:
                app.logger.error(f"Error accessing Google Doc: {e}")
                flash(f'Error accessing Google Doc: {str(e)}', 'danger')
        
        # Handle Google Sheets
        elif form.input_type.data == 'gsheet':
            sheet_id = form.google_sheet_id.data
            try:
                content = get_google_sheets_content(current_user.id, sheet_id)
                links = extract_links(content)
                
                if not links:
                    flash('No valid media links found in the Google Sheet.', 'warning')
                    return render_template('add_placement.html', form=form)
                
                # Parse and save links (same as above)
                added_count = 0
                for link in links:
                    placement_data = parse_media_links(link)
                    if placement_data:
                        placement = MediaPlacement(
                            url=link,
                            title=placement_data.get('title', ''),
                            source=placement_data.get('source', ''),
                            publication_date=placement_data.get('date'),
                            media_type=placement_data.get('type', 'article'),
                            user_id=current_user.id
                        )
                        db.session.add(placement)
                        added_count += 1
                
                if added_count > 0:
                    db.session.commit()
                    flash(f'Successfully added {added_count} media placements from Google Sheet!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Could not extract media information from the links in the Google Sheet.', 'warning')
            except Exception as e:
                app.logger.error(f"Error accessing Google Sheet: {e}")
                flash(f'Error accessing Google Sheet: {str(e)}', 'danger')
        
    return render_template('add_placement.html', form=form)

@app.route('/placement/<int:placement_id>')
@login_required
def view_placement(placement_id):
    placement = MediaPlacement.query.filter_by(id=placement_id, user_id=current_user.id).first_or_404()
    return render_template('view_placement.html', placement=placement)

@app.route('/placement/<int:placement_id>/delete', methods=['POST'])
@login_required
def delete_placement(placement_id):
    placement = MediaPlacement.query.filter_by(id=placement_id, user_id=current_user.id).first_or_404()
    db.session.delete(placement)
    db.session.commit()
    flash('Media placement deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    google_form = GoogleCredentialForm()
    
    # Check if user already has Google credentials
    google_cred = GoogleCredential.query.filter_by(user_id=current_user.id).first()
    
    if google_form.validate_on_submit():
        if google_cred:
            google_cred.api_key = google_form.api_key.data
            flash('Google API Key updated successfully!', 'success')
        else:
            google_cred = GoogleCredential(
                user_id=current_user.id,
                api_key=google_form.api_key.data
            )
            db.session.add(google_cred)
            flash('Google API Key added successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('settings'))
    
    # Pre-populate form if credentials exist
    if google_cred and request.method == 'GET':
        google_form.api_key.data = google_cred.api_key
        
    return render_template('settings.html', google_form=google_form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error='An internal error occurred'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
