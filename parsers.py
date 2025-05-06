import re
from urllib.parse import urlparse
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import logging

# Setup logger
logger = logging.getLogger(__name__)

def extract_links(text):
    """Extract all URLs from text content."""
    # URL regex pattern
    url_pattern = r'https?://[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/|\.|\|))'
    
    # Find all matches
    links = re.findall(url_pattern, text)
    
    # Clean and deduplicate links
    unique_links = set()
    for link in re.finditer(url_pattern, text):
        url = link.group(0)
        # Remove trailing punctuation that might be part of the matched URL but not the actual URL
        url = url.rstrip('.,;:!?\'\"')
        unique_links.add(url)
    
    return list(unique_links)

def parse_media_links(url):
    """
    Parse media links to extract metadata like title, source, publication date, etc.
    Returns a dictionary with the extracted information.
    """
    result = {
        'title': '',
        'source': '',
        'date': None,
        'type': 'article'
    }
    
    try:
        # Get domain name for source
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        
        result['source'] = domain
        
        # Identify media type based on domain
        if any(x in domain for x in ['youtube', 'vimeo', 'dailymotion']):
            result['type'] = 'video'
        elif any(x in domain for x in ['spotify', 'apple.com/podcast', 'soundcloud']):
            result['type'] = 'podcast'
        elif any(x in domain for x in ['twitter', 'facebook', 'instagram', 'linkedin']):
            result['type'] = 'social'
        
        # Try to fetch the page and extract metadata
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to get title from metadata first, then from title tag
            title = None
            meta_title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'title'})
            if meta_title:
                title = meta_title.get('content')
            
            if not title:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.string
            
            if title:
                result['title'] = title.strip()
            
            # Try to get publication date
            date = None
            # Check various metadata tags for publication date
            for meta_tag in soup.find_all('meta'):
                if meta_tag.get('property') in ['article:published_time', 'og:published_time'] or \
                   meta_tag.get('name') in ['pubdate', 'publishdate', 'date', 'DC.date.issued']:
                    date_str = meta_tag.get('content')
                    if date_str:
                        try:
                            date = parse_date_string(date_str)
                            if date:
                                result['date'] = date
                                break
                        except:
                            continue
            
            # If no date found in metadata, try to find it in the content
            if not result['date']:
                # Look for common date patterns in the text
                date_patterns = [
                    r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                    r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
                    r'([A-Z][a-z]+ \d{1,2}, \d{4})'  # Month DD, YYYY
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, response.text)
                    if date_match:
                        try:
                            date = parse_date_string(date_match.group(0))
                            if date:
                                result['date'] = date
                                break
                        except:
                            continue
        
        except Exception as e:
            logger.warning(f"Error fetching or parsing URL {url}: {str(e)}")
            # If we can't fetch the page, just use what we have
            pass
        
        return result
    
    except Exception as e:
        logger.error(f"Unexpected error parsing media link {url}: {str(e)}")
        return result

def parse_date_string(date_str):
    """
    Try to parse a date string in various formats.
    Returns a datetime.date object if successful, None otherwise.
    """
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.date()
        except ValueError:
            continue
    
    return None
