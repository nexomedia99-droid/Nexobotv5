import os
import logging
from dotenv import load_dotenv

load_dotenv()  # baca file .env
print("DEBUG BOT_TOKEN:", os.getenv("BOT_TOKEN"))
print("DEBUG GEMINI_API_KEY:", os.getenv("GEMINI_API_KEY"))
print("DEBUG OWNER_ID:", os.getenv("OWNER_ID"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
BOT_USERNAME = "Nexobuzz_bot"
GROUP_ID = os.getenv("GROUP_ID", "").strip() 
BUZZER_TOPIC_ID = 3
INFLUENCER_TOPIC_ID = 4
PAYMENT_TOPIC_ID = 5
PROMOTE_TOPIC_ID = 11


try:
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
except ValueError:
    OWNER_ID = 0
    logger.warning("OWNER_ID is not a valid integer, defaulting to 0")

def ensure_env():
    """Ensure all required environment variables are set"""
    missing = []

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if OWNER_ID == 0:
        missing.append("OWNER_ID")

    if missing:
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("✅ All required environment variables are configured")

def format_currency(amount):
    """Format currency for Indonesian Rupiah"""
    return f"Rp {amount:,}".replace(',', '.')

def validate_phone_number(phone):
    """Validate Indonesian phone number format"""
    phone = phone.strip().replace(' ', '').replace('-', '')
    
    # Remove +62 or 62 prefix
    if phone.startswith('+62'):
        phone = '0' + phone[3:]
    elif phone.startswith('62'):
        phone = '0' + phone[2:]
    
    # Check if starts with 08 and has proper length
    if phone.startswith('08') and 10 <= len(phone) <= 13:
        return phone
    
    return None

def sanitize_input(text, max_length=1000):
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    # Strip whitespace and limit length
    text = text.strip()[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '`']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text

def log_error(error, context="Unknown"):
    """Log errors with context"""
    logger.error(f"Error in {context}: {str(error)}")
    
def get_user_display_name(user):
    """Get display name for user"""
    if user.username:
        return f"@{user.username}"
    elif user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    else:
        return f"User {user.id}"
