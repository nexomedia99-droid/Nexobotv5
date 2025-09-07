
import hashlib
import secrets
import time
from functools import wraps

# Rate limiting
user_last_action = {}
RATE_LIMIT_SECONDS = 2

def rate_limit(func):
    @wraps(func)
    async def wrapper(update, context):
        user_id = str(update.effective_user.id)
        current_time = time.time()
        
        if user_id in user_last_action:
            if current_time - user_last_action[user_id] < RATE_LIMIT_SECONDS:
                await update.message.reply_text("⚠️ Terlalu cepat! Tunggu sebentar.")
                return
        
        user_last_action[user_id] = current_time
        return await func(update, context)
    return wrapper

def hash_sensitive_data(data):
    """Hash sensitive data before storing"""
    return hashlib.sha256(data.encode()).hexdigest()

def generate_secure_token():
    """Generate secure tokens for transactions"""
    return secrets.token_urlsafe(32)
