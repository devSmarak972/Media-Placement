// Google integration functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Google document selection UI if present
    initializeGoogleDocSelector();
    initializeGoogleSheetSelector();
    
    // Initialize OAuth redirect handling (if we're returning from Google OAuth flow)
    handleOAuthRedirect();
});

/**
 * Initialize Google Doc selector UI
 */
function initializeGoogleDocSelector() {
    const docInput = document.getElementById('google_doc_id');
    if (!docInput) return;
    
    // Add event listener to extract document ID from pasted URLs
    docInput.addEventListener('input', function() {
        const value = this.value.trim();
        
        // Extract document ID from Google Docs URL
        if (value.includes('docs.google.com')) {
            const match = value.match(/\/d\/([a-zA-Z0-9-_]+)/);
            if (match && match[1]) {
                this.value = match[1];
            }
        }
    });
    
    // Add validation feedback
    docInput.addEventListener('blur', function() {
        const value = this.value.trim();
        
        if (value && !/^[a-zA-Z0-9-_]+$/.test(value)) {
            this.classList.add('is-invalid');
            
            // Check if error message exists, if not create one
            let errorElement = document.getElementById('doc-id-error');
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.id = 'doc-id-error';
                errorElement.className = 'invalid-feedback';
                errorElement.textContent = 'Please enter a valid Google Doc ID.';
                this.parentNode.appendChild(errorElement);
            }
        } else {
            this.classList.remove('is-invalid');
            
            // Remove error message if it exists
            const errorElement = document.getElementById('doc-id-error');
            if (errorElement) {
                errorElement.remove();
            }
        }
    });
}

/**
 * Initialize Google Sheet selector UI
 */
function initializeGoogleSheetSelector() {
    const sheetInput = document.getElementById('google_sheet_id');
    if (!sheetInput) return;
    
    // Add event listener to extract spreadsheet ID from pasted URLs
    sheetInput.addEventListener('input', function() {
        const value = this.value.trim();
        
        // Extract spreadsheet ID from Google Sheets URL
        if (value.includes('spreadsheets')) {
            const match = value.match(/\/d\/([a-zA-Z0-9-_]+)/);
            if (match && match[1]) {
                this.value = match[1];
            }
        }
    });
    
    // Add validation feedback
    sheetInput.addEventListener('blur', function() {
        const value = this.value.trim();
        
        if (value && !/^[a-zA-Z0-9-_]+$/.test(value)) {
            this.classList.add('is-invalid');
            
            // Check if error message exists, if not create one
            let errorElement = document.getElementById('sheet-id-error');
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.id = 'sheet-id-error';
                errorElement.className = 'invalid-feedback';
                errorElement.textContent = 'Please enter a valid Google Sheet ID.';
                this.parentNode.appendChild(errorElement);
            }
        } else {
            this.classList.remove('is-invalid');
            
            // Remove error message if it exists
            const errorElement = document.getElementById('sheet-id-error');
            if (errorElement) {
                errorElement.remove();
            }
        }
    });
}

/**
 * Handle OAuth redirect from Google
 */
function handleOAuthRedirect() {
    // Check if we have a state and code parameter in the URL (OAuth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const state = urlParams.get('state');
    const code = urlParams.get('code');
    const error = urlParams.get('error');
    
    // If we have an error, display it
    if (error) {
        createAlertBanner('danger', 'Google Authentication Error', 
            error === 'access_denied' 
                ? 'You denied access to your Google account. Please try again.' 
                : `Error authenticating with Google: ${error}`
        );
        
        // Remove parameters from URL
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
        return;
    }
    
    // If we have state and code, we're returning from OAuth
    if (state && code) {
        // Show loading indicator
        createAlertBanner('info', 'Processing Google Authentication', 
            'Completing the authentication process...', true);
        
        // The actual processing is handled server-side through the callback route
        
        // Remove parameters from URL - but let the server handle the redirect
        // since it needs these parameters
    }
}

/**
 * Create an alert banner with a message
 * @param {string} type - Bootstrap alert type ('success', 'danger', 'warning', 'info')
 * @param {string} title - Alert title
 * @param {string} message - Alert message
 * @param {boolean} persistent - Whether the alert should persist (not auto-dismiss)
 */
function createAlertBanner(type, title, message, persistent = false) {
    // Find or create alert container
    let alertContainer = document.getElementById('alert-container');
    
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.className = 'container mt-3';
        
        // Insert after the navbar
        const navbar = document.querySelector('nav');
        if (navbar && navbar.nextSibling) {
            navbar.parentNode.insertBefore(alertContainer, navbar.nextSibling);
        } else {
            document.body.insertBefore(alertContainer, document.body.firstChild);
        }
    }
    
    // Create alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show` + (persistent ? ' alert-persistent' : '');
    alert.role = 'alert';
    
    const titleElement = title ? `<strong>${title}:</strong> ` : '';
    alert.innerHTML = `
        ${titleElement}${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertContainer.appendChild(alert);
    
    // Initialize dismiss button
    const closeButton = alert.querySelector('.btn-close');
    closeButton.addEventListener('click', function() {
        alert.remove();
    });
    
    // Auto-dismiss non-persistent alerts
    if (!persistent) {
        setTimeout(function() {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    }
    
    return alert;
}
