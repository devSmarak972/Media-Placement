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
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + '...'

def take_screenshot(url, output_path=None, timeout=15):
    """
    Take a screenshot of a webpage using Selenium WebDriver with optimized settings.
    
    Args:
        url (str): The URL of the webpage to screenshot
        output_path (str, optional): Path to save the screenshot. If None, returns the image bytes.
        timeout (int): Maximum seconds to wait for page load.
        
    Returns:
        bytes or str: If output_path is None, returns the screenshot as bytes, otherwise returns the path.
    """
    import io
    import os
    import time
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    # Set up Chrome options with optimized performance
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,1024')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--blink-settings=imagesEnabled=true')
    chrome_options.add_argument('--disable-logging')
    chrome_options.page_load_strategy = 'eager'  # Interactive instead of complete load
    
    try:
        # Initialize the Chrome driver with a timeout
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.set_page_load_timeout(timeout)
        
        # Navigate to the URL
        try:
            driver.get(url)
            
            # Wait less time for the page to become somewhat interactive
            time.sleep(2)
            
            # Scroll down to capture more content
            driver.execute_script("window.scrollTo(0, 250)")
            
            # Take screenshot
            if output_path:
                driver.save_screenshot(output_path)
                result = output_path
            else:
                # Return as bytes
                result = driver.get_screenshot_as_png()
                
            driver.quit()
            return result
            
        except Exception as e:
            print(f"Timed out or error loading page: {str(e)}")
            # Still try to take a screenshot of what loaded
            if output_path:
                driver.save_screenshot(output_path)
                result = output_path
            else:
                result = driver.get_screenshot_as_png()
                
            driver.quit()
            return result
            
    except Exception as e:
        print(f"Error setting up webdriver: {str(e)}")
        return None
