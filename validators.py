
import re
from urllib.parse import urlparse

def validate_url(url):
    """Validate URL format and safety"""
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        
        # Block suspicious domains
        blocked_domains = ['bit.ly', 'tinyurl.com']  # Add more as needed
        if any(domain in result.netloc for domain in blocked_domains):
            return False
            
        return True
    except:
        return False

def validate_username(username):
    """Enhanced username validation"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    
    # Only allow alphanumeric, underscore, and hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False
    
    # Block reserved usernames
    reserved = ['admin', 'bot', 'system', 'nexo', 'buzz']
    if username.lower() in reserved:
        return False
        
    return True

def sanitize_text(text, max_length=1000):
    """Enhanced text sanitization"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Limit length
    text = text[:max_length]
    
    # Remove potentially dangerous HTML/markdown
    dangerous_patterns = [
        r'<script.*?</script>',
        r'javascript:',
        r'onclick=',
        r'onerror=',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()
