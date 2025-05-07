import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, redirect, url_for, request, flash, session, current_app
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from models import db, GoogleCredential

google_bp = Blueprint('google', __name__, url_prefix='/google')

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
    flow.fetch_token(authorization_response=request.url)
    
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
    
    flash('Successfully authenticated with Google!', 'success')
    return redirect(url_for('settings'))
