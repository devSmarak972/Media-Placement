// Main JavaScript file for common functionality across the application

// Initialize any components that need JavaScript activation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-persistent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // External link handler - add target="_blank" to external links
    document.querySelectorAll('a[href^="http"]').forEach(function(link) {
        if (!link.getAttribute('target')) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        }
    });
    
    // Form validation styles
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function() {
            form.classList.add('was-validated');
        });
    });
});

// Utility functions

/**
 * Format a date string for display
 * @param {string} dateString - Date string in ISO format (YYYY-MM-DD)
 * @param {string} format - Format type ('short', 'long', or 'relative')
 * @returns {string} Formatted date string
 */
function formatDate(dateString, format = 'short') {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    
    if (isNaN(date.getTime())) return dateString;
    
    if (format === 'short') {
        return date.toLocaleDateString();
    } else if (format === 'long') {
        return date.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } else if (format === 'relative') {
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else if (diffDays < 30) {
            const diffWeeks = Math.floor(diffDays / 7);
            return `${diffWeeks} week${diffWeeks > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    return dateString;
}

/**
 * Truncate text with ellipsis if it exceeds a certain length
 * @param {string} text - The text to truncate
 * @param {number} maxLength - Maximum length before truncation
 * @returns {string} Truncated text with ellipsis if needed
 */
function truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    
    return text.substring(0, maxLength) + '...';
}

/**
 * Get domain name from URL
 * @param {string} url - URL to extract domain from
 * @returns {string} Domain name
 */
function getDomainFromUrl(url) {
    if (!url) return '';
    
    try {
        const urlObj = new URL(url);
        let domain = urlObj.hostname;
        
        // Remove 'www.' prefix if present
        if (domain.startsWith('www.')) {
            domain = domain.substring(4);
        }
        
        return domain;
    } catch (e) {
        // If URL parsing fails, try a simple regex
        const match = url.match(/^(?:https?:\/\/)?(?:www\.)?([^\/]+)/i);
        return match ? match[1] : url;
    }
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise} Promise that resolves when copying is complete
 */
function copyToClipboard(text) {
    // Modern approach using Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
    }
    
    // Fallback for older browsers
    return new Promise((resolve, reject) => {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        
        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textarea);
            if (successful) {
                resolve();
            } else {
                reject(new Error('Copy command was unsuccessful'));
            }
        } catch (err) {
            document.body.removeChild(textarea);
            reject(err);
        }
    });
}
