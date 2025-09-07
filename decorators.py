from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from utils import OWNER_ID
import logging

logger = logging.getLogger(__name__)

def admin_only(func):
    """Decorator to restrict commands to admin only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        if user_id != OWNER_ID:
            logger.warning(f"Unauthorized admin command access by {username} (ID: {user_id})")
            await update.message.reply_text(
                "🚫 *Akses Ditolak*\n\n"
                "Kamu tidak memiliki akses untuk menggunakan perintah admin ini.\n\n"
                "Hanya owner yang dapat menggunakan fitur ini.",
                parse_mode="Markdown"
            )
            return
        
        logger.info(f"Admin command executed by {username} (ID: {user_id}): {func.__name__}")
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def registered_only(func):
    """Decorator to restrict commands to registered users only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from db import get_user_by_id
        
        user_id = str(update.effective_user.id)
        user_data = get_user_by_id(user_id)
        
        if not user_data:
            await update.message.reply_text(
                "❌ *Registrasi Diperlukan*\n\n"
                "Kamu harus mendaftar sebagai member terlebih dahulu untuk menggunakan fitur ini.\n\n"
                "👉 Ketik `/register` untuk memulai pendaftaran.",
                parse_mode="Markdown"
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def group_only(func):
    """Decorator to restrict commands to group chats only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type not in ["group", "supergroup"]:
            await update.message.reply_text(
                "👥 Perintah ini hanya bisa digunakan di grup.\n\n"
                "Silakan gunakan di grup NexoBuzz."
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def private_only(func):
    """Decorator to restrict commands to private chats only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type != "private":
            await update.message.reply_text(
                "🔒 Perintah ini hanya bisa digunakan di private chat.\n\n"
                "Silakan DM bot untuk menggunakan fitur ini."
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def rate_limit(max_calls=5, window=60):
    """Decorator to implement rate limiting"""
    call_counts = {}
    
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            import time
            
            user_id = update.effective_user.id
            current_time = time.time()
            
            # Clean old entries
            call_counts[user_id] = [
                call_time for call_time in call_counts.get(user_id, [])
                if current_time - call_time < window
            ]
            
            # Check rate limit
            if len(call_counts.get(user_id, [])) >= max_calls:
                await update.message.reply_text(
                    "⏱️ *Rate Limit Exceeded*\n\n"
                    f"Kamu sudah menggunakan perintah ini {max_calls} kali dalam {window} detik terakhir.\n\n"
                    "Silakan tunggu sebentar sebelum mencoba lagi.",
                    parse_mode="Markdown"
                )
                return
            
            # Record this call
            call_counts.setdefault(user_id, []).append(current_time)
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator
