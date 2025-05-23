import os
import json
import io
import base64
from datetime import datetime, timedelta
from flask import Blueprint, redirect, url_for, request, flash, session, current_app, render_template
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

from models import db, GoogleCredential, MediaPlacement

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprints
google_bp = Blueprint('google', __name__, url_prefix='/google')
docket_bp = Blueprint('docket', __name__, url_prefix='/docket')

def get_google_credentials():
    """Get Google credentials."""
    google_cred = GoogleCredential.query.first()
    
    if not google_cred or (not google_cred.api_key and not google_cred.oauth_token):
        raise ValueError("No Google credentials found. Please add your API key in settings.")
    
    return google_cred

def get_google_service(service_name, version='v1'):
    """Create and return a Google API service instance."""
    google_cred = get_google_credentials()
    
    # If using API key
    if google_cred.api_key:
        return build(
            service_name, 
            version, 
            developerKey=google_cred.api_key
        )
    
    # If using OAuth token
    elif google_cred.oauth_token:
        # Check if token is expired
        if google_cred.token_expiry and google_cred.token_expiry < datetime.utcnow():
            # Refresh token if we have a refresh token
            if google_cred.refresh_token:
                refresh_google_token(google_cred)
            else:
                raise ValueError("OAuth token has expired. Please re-authenticate with Google.")
        
        # Create credentials object from stored token
        token_data = json.loads(google_cred.oauth_token)
        credentials = Credentials(
            token=token_data.get('access_token'),
            refresh_token=google_cred.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=current_app.config['GOOGLE_CLIENT_ID'],
            client_secret=current_app.config['GOOGLE_CLIENT_SECRET'],
            scopes=current_app.config['GOOGLE_AUTH_SCOPES']
        )
        
        return build(service_name, version, credentials=credentials)
    
    else:
        raise ValueError("No valid Google authentication method found.")

def refresh_google_token(google_cred):
    """Refresh an expired OAuth token."""
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        'refresh_token': google_cred.refresh_token,
        'client_id': current_app.config['GOOGLE_CLIENT_ID'],
        'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
        'grant_type': 'refresh_token'
    }
    
    response = requests.post(token_url, data=payload)
    
    if response.status_code == 200:
        token_data = response.json()
        token_info = {
            'access_token': token_data['access_token'],
            'token_type': token_data['token_type'],
            'expires_in': token_data['expires_in']
        }
        
        # Update stored token
        google_cred.oauth_token = json.dumps(token_info)
        google_cred.token_expiry = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        db.session.commit()
    else:
        # Token refresh failed
        raise ValueError(f"Failed to refresh Google token: {response.text}")

def get_google_docs_content(doc_id):
    """Retrieve content from a Google Doc."""
    try:
        docs_service = get_google_service('docs', 'v1')
        document = docs_service.documents().get(documentId=doc_id).execute()
        
        content = ""
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for paragraph_element in element['paragraph'].get('elements', []):
                    if 'textRun' in paragraph_element:
                        content += paragraph_element['textRun'].get('content', '')
        
        return content
    except HttpError as error:
        current_app.logger.error(f"Error accessing Google Doc: {error}")
        raise ValueError(f"Error accessing Google Doc: {error.reason}")
    except Exception as e:
        current_app.logger.error(f"Unexpected error with Google Docs: {e}")
        raise ValueError(f"Error accessing Google Doc: {str(e)}")

def get_google_sheets_content(sheet_id):
    """Retrieve content from a Google Sheet."""
    try:
        sheets_service = get_google_service('sheets', 'v4')
        sheet = sheets_service.spreadsheets().get(spreadsheetId=sheet_id, includeGridData=True).execute()
        
        content = ""
        for sheet_data in sheet.get('sheets', []):
            grid_data = sheet_data.get('data', [])
            for grid in grid_data:
                for row in grid.get('rowData', []):
                    for cell in row.get('values', []):
                        if 'formattedValue' in cell:
                            content += cell['formattedValue'] + " "
                    content += "\n"
        
        return content
    except HttpError as error:
        current_app.logger.error(f"Error accessing Google Sheet: {error}")
        raise ValueError(f"Error accessing Google Sheet: {error.reason}")
    except Exception as e:
        current_app.logger.error(f"Unexpected error with Google Sheets: {e}")
        raise ValueError(f"Error accessing Google Sheet: {str(e)}")

@google_bp.route('/auth')
def google_auth():
    # Create flow instance to manage OAuth flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": current_app.config['GOOGLE_CLIENT_ID'],
                "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [current_app.config['GOOGLE_REDIRECT_URI']]
            }
        },
        scopes=current_app.config['GOOGLE_AUTH_SCOPES']
    )
    
    # Set the redirect URI
    flow.redirect_uri = current_app.config['GOOGLE_REDIRECT_URI']
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Store state in session for later validation
    session['google_auth_state'] = state
    
    # Redirect to Google's OAuth consent screen
    return redirect(authorization_url)

@google_bp.route('/auth/callback')
def google_auth_callback():
    # Verify state matches to prevent CSRF attacks
    state = session.get('google_auth_state')
    if not state or state != request.args.get('state'):
        flash('Authentication failed: State verification failed.', 'danger')
        return redirect(url_for('settings'))
    
    # Create flow instance with the stored state
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": current_app.config['GOOGLE_CLIENT_ID'],
                "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [current_app.config['GOOGLE_REDIRECT_URI']]
            }
        },
        scopes=current_app.config['GOOGLE_AUTH_SCOPES'],
        state=state
    )
    flow.redirect_uri = current_app.config['GOOGLE_REDIRECT_URI']
    
    # Use authorization code to get token
    # In Replit, the URL might be using HTTP while the external URL is HTTPS
    # Fix the URL protocol to match the redirect URI protocol
    auth_response = request.url
    if current_app.config['GOOGLE_REDIRECT_URI'].startswith('https') and auth_response.startswith('http:'):
        auth_response = auth_response.replace('http:', 'https:', 1)
        
    logger.info(f"Using authorization response: {auth_response}")
    flow.fetch_token(authorization_response=auth_response)
    
    # Get credentials from flow
    credentials = flow.credentials
    
    # Store credentials in database
    google_cred = GoogleCredential.query.first()
    
    token_data = {
        'access_token': credentials.token,
        'token_type': 'Bearer',
        'expires_in': 3600  # Default expiry of 1 hour
    }
    
    token_expiry = datetime.utcnow() + timedelta(seconds=3600)
    
    if google_cred:
        google_cred.oauth_token = json.dumps(token_data)
        google_cred.refresh_token = credentials.refresh_token
        google_cred.token_expiry = token_expiry
    else:
        google_cred = GoogleCredential(
            oauth_token=json.dumps(token_data),
            refresh_token=credentials.refresh_token,
            token_expiry=token_expiry
        )
        db.session.add(google_cred)
    
    db.session.commit()
    
    # Check if there's a return_to session variable to handle redirects
    # This is used when coming from specific processes that need OAuth
    return_to = session.pop('return_to', None)
    if return_to == 'create_dockets':
        flash('Successfully authenticated with Google! Creating dockets...', 'success')
        return redirect(url_for('docket.create_all_dockets'))
    elif return_to == 'export_sheet':
        flash('Successfully authenticated with Google! Exporting to sheet...', 'success')
        return redirect(url_for('docket.export_to_sheet'))
    
    # Default: return to settings page with success message
    flash('Successfully authenticated with Google!', 'success')
    return render_template('google_auth_success.html')
def take_screenshot(url, output_path=None, timeout=15):
    """
    Take a screenshot of a webpage using Selenium WebDriver with Chromium (Docker-optimized).

    Args:
        url (str): The URL of the webpage to screenshot.
        output_path (str, optional): Path to save the screenshot. If None, returns the image bytes.
        timeout (int): Maximum seconds to wait for page load.

    Returns:
        bytes or str: Screenshot bytes if output_path is None, otherwise the output path.
    """
    import time
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    # Set up options for Chromium
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,1024')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--blink-settings=imagesEnabled=true')
    options.page_load_strategy = 'eager'

    try:
        # Create the driver using system-installed chromedriver
        driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)
        driver.set_page_load_timeout(timeout)

        try:
            driver.get(url)
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 250)")

            if output_path:
                driver.save_screenshot(output_path)
                result = output_path
            else:
                result = driver.get_screenshot_as_png()

        except Exception as e:
            print(f"Timed out or error loading page: {str(e)}")
            # Attempt screenshot of partial content
            if output_path:
                driver.save_screenshot(output_path)
                result = output_path
            else:
                result = driver.get_screenshot_as_png()
        finally:
            driver.quit()

        return result

    except Exception as e:
        print(f"Error setting up WebDriver: {str(e)}")
        return None

def create_google_doc(title, content, screenshot=None):
    """Create a Google Doc with the given content and screenshot."""
    try:
        docs_service = get_google_service('docs', 'v1')
        drive_service = get_google_service('drive', 'v3')
        
        # Create a new document
        doc = {
            'title': title
        }
        doc = docs_service.documents().create(body=doc).execute()
        doc_id = doc.get('documentId')
        
        # Prepare the content
        requests = [{
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': content
            }
        }]
        
        # Update the document with content
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        # If there's a screenshot, insert it
        if screenshot:
            # Upload screenshot to drive first
            file_metadata = {
                'name': f'{title} Screenshot',
                'mimeType': 'image/png'
            }
            
            # Convert screenshot to Media object
            screenshot_bytes = io.BytesIO(screenshot)
            media = MediaIoBaseUpload(screenshot_bytes, mimetype='image/png', resumable=True)
            
            # Upload file
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            # Get the fileId and create an image in the document
            file_id = file.get('id')
            
            # Now insert the image into the document
            requests = [{
                'insertInlineImage': {
                    'location': {
                        'index': 1  # Insert at the beginning
                    },
                    'uri': f'https://drive.google.com/uc?id={file_id}',
                    'objectSize': {
                        'height': {
                            'magnitude': 400,
                            'unit': 'PT'
                        },
                        'width': {
                            'magnitude': 600,
                            'unit': 'PT'
                        }
                    }
                }
            }]
            
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
        
        # Return the document URL
        return f"https://docs.google.com/document/d/{doc_id}/edit"
    
    except Exception as e:
        logger.error(f"Error creating Google Doc: {str(e)}")
        raise ValueError(f"Error creating Google Doc: {str(e)}")

def create_google_sheet(title, data):
    """Create a Google Sheet with the given data."""
    try:
        sheets_service = get_google_service('sheets', 'v4')
        drive_service = get_google_service('drive', 'v3')
        
        # Create a new spreadsheet
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        
        # Prepare the data for the sheet
        values = [
            ["Title", "URL", "Source", "Publication Date", "Media Type", "Docket Link"]
        ]
        values.extend(data)
        
        # Update spreadsheet with data
        body = {
            'values': values
        }
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Sheet1!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Format header row
        requests = [{
            'updateCells': {
                'rows': {
                    'values': [{
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.7,
                                'green': 0.7,
                                'blue': 0.7
                            },
                            'textFormat': {
                                'bold': True
                            }
                        }
                    }]
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)',
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                }
            }
        }]
        
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        # Return the spreadsheet URL
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    
    except Exception as e:
        logger.error(f"Error creating Google Sheet: {str(e)}")
        raise ValueError(f"Error creating Google Sheet: {str(e)}")

@docket_bp.route('/create/<int:placement_id>')
def create_docket(placement_id):
    """Create a docket for a specific media placement."""
    try:
        # Check if Google credentials are available
        try:
            google_cred = get_google_credentials()
            if not google_cred.oauth_token:
                # Store where to return after OAuth
                session['return_to'] = 'create_dockets'
                flash('Please authenticate with Google before creating dockets.', 'warning')
                return redirect(url_for('google.google_auth'))
        except ValueError:
            # Store where to return after OAuth
            session['return_to'] = 'create_dockets'
            flash('Please authenticate with Google before creating dockets.', 'warning')
            return redirect(url_for('google.google_auth'))
        
        # Get the placement
        placement = MediaPlacement.query.filter_by(id=placement_id).first_or_404()
        
        # Take a screenshot
        screenshot = take_screenshot(placement.url)
        
        # Extract a summary
        summary = extract_summary(placement.url)
        
        # Create the document content
        content = f"""
# {placement.title or "Untitled Article"}

URL: {placement.url}
Source: {placement.source}
Publication Date: {placement.publication_date if placement.publication_date else "Unknown"}
Media Type: {placement.media_type}
Created: {placement.created_at.strftime('%Y-%m-%d %H:%M:%S')}

## Summary
{summary}

## Notes
{placement.notes or ""}
"""
        
        # Create a Google Doc
        doc_title = f"Media Placement - {placement.title or placement.source or 'Untitled'}"
        doc_url = create_google_doc(
            doc_title,
            content,
            screenshot
        )
        
        # Update the placement with the doc URL
        placement.docket_url = doc_url
        db.session.commit()
        
        # Return the success template
        return render_template('docket_success.html', 
                               docket_url=doc_url, 
                               docket_title=doc_title)
        
    except Exception as e:
        logger.error(f"Error creating docket: {str(e)}")
        flash(f'Error creating docket: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@docket_bp.route('/create_all')
def create_all_dockets():
    """Create dockets for all media placements."""
    try:
        # Check if Google credentials are available
        try:
            google_cred = get_google_credentials()
            if not google_cred.oauth_token:
                # Store where to return after OAuth
                session['return_to'] = 'create_dockets'
                flash('Please authenticate with Google before creating dockets.', 'warning')
                return redirect(url_for('google.google_auth'))
        except ValueError:
            # Store where to return after OAuth
            session['return_to'] = 'create_dockets'
            flash('Please authenticate with Google before creating dockets.', 'warning')
            return redirect(url_for('google.google_auth'))
        
        # Get all placements that don't have dockets yet
        placements = MediaPlacement.query.filter(MediaPlacement.docket_url == None).all()
        
        if not placements:
            flash('No media placements found that need dockets.', 'info')
            return redirect(url_for('dashboard'))
        
        docket_data = []
        success_count = 0
        
        for placement in placements:
            try:
                # Take a screenshot
                screenshot = take_screenshot(placement.url)
                
                # Extract a summary
                summary = extract_summary(placement.url)
                
                # Create the document content
                content = f"""
# {placement.title or "Untitled Article"}

URL: {placement.url}
Source: {placement.source}
Publication Date: {placement.publication_date if placement.publication_date else "Unknown"}
Media Type: {placement.media_type}
Created: {placement.created_at.strftime('%Y-%m-%d %H:%M:%S')}

## Summary
{summary}

## Notes
{placement.notes or ""}
"""
                
                # Create a Google Doc
                doc_title = f"Media Placement - {placement.title or placement.source or 'Untitled'}"
                doc_url = create_google_doc(
                    doc_title,
                    content,
                    screenshot
                )
                
                # Update the placement with the doc URL
                placement.docket_url = doc_url
                db.session.commit()
                
                # Add to spreadsheet data
                docket_data.append([
                    placement.title or "Untitled",
                    placement.url,
                    placement.source,
                    str(placement.publication_date) if placement.publication_date else "Unknown",
                    placement.media_type,
                    doc_url
                ])
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error creating docket for placement {placement.id}: {str(e)}")
                continue
        
        # Create a Google Sheet with all dockets
        if docket_data:
            sheet_title = "Media Placements Summary"
            sheet_url = create_google_sheet(sheet_title, docket_data)
            
            flash(f'Successfully created {success_count} dockets and a summary spreadsheet!', 'success')
            
            # Return with sheet URL for download and info about created dockets
            return render_template('docket_success.html', 
                                   docket_title="Multiple Media Placement Dockets",
                                   docket_url=sheet_url,
                                   item_count=success_count)
        else:
            flash('No dockets were created due to errors. Please check the logs.', 'warning')
            return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Error creating dockets: {str(e)}")
        flash(f'Error creating dockets: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@docket_bp.route('/export_to_sheet')
def export_to_sheet():
    """Export all media placements to a Google Sheet."""
    try:
        # Check if Google credentials are available
        try:
            google_cred = get_google_credentials()
            if not google_cred.oauth_token:
                # Store where to return after OAuth
                session['return_to'] = 'export_sheet'
                flash('Please authenticate with Google before exporting to sheet.', 'warning')
                return redirect(url_for('google.google_auth'))
        except ValueError:
            # Store where to return after OAuth
            session['return_to'] = 'export_sheet'
            flash('Please authenticate with Google before exporting to sheet.', 'warning')
            return redirect(url_for('google.google_auth'))
        
        # Get all placements
        placements = MediaPlacement.query.all()
        
        if not placements:
            flash('No media placements found to export.', 'info')
            return redirect(url_for('dashboard'))
        
        # Prepare data for sheet
        sheet_data = []
        for placement in placements:
            sheet_data.append([
                placement.title or "Untitled",
                placement.url,
                placement.source,
                str(placement.publication_date) if placement.publication_date else "Unknown",
                placement.media_type,
                placement.docket_url or "No docket"
            ])
        
        # Create the sheet
        sheet_title = "Media Placements Export"
        sheet_url = create_google_sheet(sheet_title, sheet_data)
        
        flash(f'Successfully exported {len(placements)} media placements to Google Sheets!', 'success')
        return render_template('export_success.html', 
                              sheet_url=sheet_url, 
                              sheet_title=sheet_title,
                              item_count=len(placements))
        
    except Exception as e:
        logger.error(f"Error exporting to sheet: {str(e)}")
        flash(f'Error exporting to sheet: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
