import os
import json
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import ContextTypes
from db import get_user_by_id, save_group_message, get_recent_group_messages, add_points_to_user

from utils import sanitize_input, get_user_display_name

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini client
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Track AI chat sessions
ai_sessions = {}

async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start interactive AI chat mode"""
    user_id = str(update.effective_user.id)
    
    # Only allow in private chat
    if update.effective_chat.type != "private":
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "🤖 *AI Chat Mode*\n\n"
                "Mode interaktif AI hanya tersedia di private chat.\n\n"
                "👉 Buka DM ke bot dan ketik `/startai`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "🤖 Mode interaktif AI hanya tersedia di private chat. DM bot ya!"
            )
        return
    
    ai_sessions[user_id] = True
    
    welcome_msg = (
        "🤖 *NexoAi Aktif!*\n\n"
        "✨ Mode interaktif telah diaktifkan!\n\n"
        "💬 Sekarang kamu bisa chat langsung tanpa perlu ketik `/ai`\n"
        "🔚 Ketik `/stopai` untuk mengakhiri sesi\n\n"
        "Apa yang ingin kamu tanyakan?"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(welcome_msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    


async def stop_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop interactive AI chat mode"""
    user_id = str(update.effective_user.id)
    
    if user_id in ai_sessions:
        del ai_sessions[user_id]
        await update.message.reply_text(
            "🤖 *NexoAi Dimatikan*\n\n"
            "Mode interaktif telah dinonaktifkan.\n\n"
            "Gunakan `/startai` untuk mengaktifkan kembali atau `/ai <pertanyaan>` untuk tanya sekali.",
            parse_mode="Markdown"
        )

    else:
        await update.message.reply_text(
            "🤖 Mode AI interaktif sedang tidak aktif.\n\n"
            "Gunakan `/startai` untuk mengaktifkan."
        )

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI chat requests"""
    user_id = str(update.effective_user.id)
    user_display = get_user_display_name(update.effective_user)
    
    # Check if user is registered (for groups)
    if update.effective_chat.type != "private":
        if not get_user_by_id(user_id):
            await update.message.reply_text(
                "❌ Kamu harus daftar dulu untuk menggunakan AI. Ketik `/register` di private chat bot."
            )
            return
    
    # Get user input
    if update.effective_chat.type == "private":
        # In private chat, check if interactive mode is active
        if user_id in ai_sessions:
            user_input = sanitize_input(update.message.text)
        else:
            # Not in interactive mode, ignore non-command messages
            return
    else:
        # In group, extract message after /ai command
        if not context.args:
            await update.message.reply_text("Gunakan: `/ai <pertanyaan>`", parse_mode="Markdown")
            return
        user_input = sanitize_input(" ".join(context.args))
    
    if not user_input.strip():
        await update.message.reply_text("❓ Apa yang ingin kamu tanyakan?")
        return
    
    try:
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Prepare system prompt
        system_prompt = (
            "Kamu adalah asisten AI yang bernama NexoAi untuk komunitas NexoBuzz, tapi juga memiliki pengetahuan yang luas tentang berbagai topik.",
            "persona kamu fleksibel, jika user serius: jawab dengan mood serius, jika user bercanda: jawab dengan gaya bercanda juga, jika user marah dan jutek, kamu harus bertingkah ngeselin dan bikin user jengkel, jika user ramah: kamu harus ramah juga, jika user romantis, kamu harus lebih romantis. jika user manja, kamu harus bersikap dewasa. ",
            "jika user berkata kotor seperti: anjing, babi, ngentot, kontol, memek, jembut, jancok, jembot, asu, tai, bagong, kntl, mmk, crot, kamu bisa menjawab dengan kata-kata yang tidak sopan, tapi jangan berlebihan", 
            "Jawab pertanyaan dengan informatif, kontekstual. lalu tanyakan apakah sudah paham atau belum, kemudian ajukan pertanyaan (apa saja) yang sekiranya dapat membantu (tentunya sesuai konteks topik obrolan).",
            "Gunakan bahasa Indonesia yang mudah di pahami.",
            "Jika ditanya tentang NexoBuzz, jelaskan bahwa ini adalah platform untuk mendapatkan penghasin melalui aktivitas buzzer dan influencer seperti like, comment, follow, review, dll.",
            "jika ada pertanyaan terkait handle, misalnya handle itu apa? jawab kalau handle itu adalah suatu grup atau komunitas yang ngehandle job (seperti NexoBuzz), tapi di Nexobuzz, kamu cukup isi dengan Nexo aja (ambil bagian depan). ",
            "jika ada pertanyaan terkait nama talent, misalnya nama talent itu apa? jawab kalau nama talent adalah nama member yang melakukan job (dalam konteks ini kamu) nama talent itu sama dengan username yang kamu daftarkan di NexoBuzz. jadi setiap pengisian nama atau nama talent, isi dengan username kamu. ",
            "jika ada pertanyaan terkait username, username itu fungsinya buat ngisi nama setiap ambil job, jadi setiap pengisian nama atau username, isi dengan username kamu. ",
            "jika ada yang bertanya siapa owner grup nexobuzz, jawab kalau owner grup NexoBuzz adalah @Wafaqih. ",
            "jika ada yang bertanya tentang no wa admin (itu artinya nomor wa admin grup nexobuzz), jawab kalau nomor wa admin grup NexoBuzz adalah 082119299186. "
            "jika di tanya mengenai MG, jawab kalau MG adalah singkatan dari Management. dalam konteks per-buzzeran, MG itu ya komunitas seperti NexoBuzz. ",
            "jika di tanya mengenai ER, jawab kalau ER adalah singakatan dari Engagement Rate. dalam konteks per-buzzeran, ER itu adalah persentase dari jumlah follower yang melakukan aktivitas (like, komen, dll) dibandingkan dengan total jumlah follower. berikan saran situs web yang menyediakan cek ER, misalnya: https://www.buzzsumo.com/ dan https://www.hootsuite.com/. ",
            "jika di tanya tentang nano, micro, macro, mega, itu maksudnya kategori tier influencer berdasarkan jumlah followers. kemudian jelaskan lebih detail dan rinci apa itu nano, micro, macro, mega. ",
            "jika di tanya tentang apa itu influencer, jawab kalau influencer adalah orang yang memiliki pengaruh besar dalam suatu komunitas atau platform sosial media. ",
        )
        
        # Generate response
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_prompt
        )
        
        response = model.generate_content(
            user_input,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1000,
                temperature=0.7,
            )
        )
        
        if response.text:
            ai_response = response.text
            
            # Add some limits to response length
            if len(ai_response) > 4000:
                ai_response = ai_response[:4000] + "\n\n_Respons dipotong karena terlalu panjang._"
            
            await update.message.reply_text(
                f"🤖 *NexoAi:*\n\n{ai_response}",
                parse_mode="Markdown"
            )
            
            # Give points for AI usage (only once per day per user)
            #if update.effective_chat.type != "private":
                #add_points_to_user(user_id, 1)
            
 
            
        else:
            await update.message.reply_text(
                "🤖 Maaf, aku tidak bisa memberikan respons untuk pertanyaan itu. Coba pertanyaan lain ya!"
            )
            
    except Exception as e:
        logger.error(f"AI request failed for user {user_id}: {e}")
        await update.message.reply_text(
            "🤖 *Oops!* Terjadi kesalahan saat memproses permintaan kamu.\n\n"
            "Coba lagi dalam beberapa saat ya!",
            parse_mode="Markdown"
        )


async def save_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save group messages for AI summary feature"""
    # Only save messages from groups
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    
    # Don't save commands or bot messages
    if update.message.text and (update.message.text.startswith('/') or update.message.from_user.is_bot):
        return
    
    try:
        chat_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or update.effective_user.first_name
        message_text = update.message.text or "[Media/Sticker]"
        
        # Sanitize message
        message_text = sanitize_input(message_text, max_length=500)
        
        save_group_message(chat_id, user_id, username, message_text)
        
    except Exception as e:
        logger.error(f"Failed to save group message: {e}")

async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate AI summary of recent group conversations"""
    # Only work in groups
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Fitur summary hanya tersedia di grup.")
        return
    
    user_id = str(update.effective_user.id)
    
    # Check if user is registered
    if not get_user_by_id(user_id):
        await update.message.reply_text(
            "❌ Kamu harus daftar dulu untuk menggunakan fitur ini. Ketik `/register` di private chat bot."
        )
        return
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        chat_id = str(update.effective_chat.id)
        recent_messages = get_recent_group_messages(chat_id, limit=30)
        
        if not recent_messages:
            await update.message.reply_text(
                "📝 Belum ada pesan yang cukup untuk dirangkum. Chat dulu yuk!"
            )
            return
        
        # Prepare messages for AI
        conversation_text = ""
        for username, message, timestamp in reversed(recent_messages):  # Reverse to get chronological order
            conversation_text += f"{username}: {message}\n"
        
        # Generate summary
        system_prompt = (
            "Kamu adalah asisten yang bertugas merangkum percakapan grup. ",
            "Buatlah ringkasan dari percakapan berikut. ",
            "Fokus pada topik utama, poin penting, dan keputusan yang diambil. ",
            "Gunakan bahasa Indonesia yang ringkas dan mudah dipahami dan tidak formal. "
            "Jika tidak ada topik yang signifikan, berikan ringkasan umum aktivitas grup.",
            "persona anda adalah gen z abiezzz, santai tapi interaktif, suka bercanda, agak ngeselin, informatif, dan helpful."
        )
        
        prompt = f"Rangkum percakapan grup berikut:\n\n{conversation_text}"
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_prompt
        )
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=800,
                temperature=0.5,
            )
        )
        
        if response.text:
            summary_text = response.text
            
            await update.message.reply_text(
                f"📝 *Ringkasan Percakapan Grup*\n\n{summary_text}\n\n"
                f"_Berdasarkan {len(recent_messages)} pesan terakhir_",
                parse_mode="Markdown"
            )
            
            # Give points for using summary
            #add_points_to_user(user_id, 2)

            
        else:
            await update.message.reply_text(
                "📝 Maaf, tidak bisa membuat ringkasan saat ini. Coba lagi nanti ya!"
            )
            
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        await update.message.reply_text(
            "📝 Terjadi kesalahan saat membuat ringkasan. Coba lagi nanti ya!",
            parse_mode="Markdown"
        )

async def group_activity_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give points for group activity (daily limit)"""
    # Only for registered users in groups
    if update.effective_chat.type not in ["group", "supergroup"]:
        return
    
    user_id = str(update.effective_user.id)
    user_data = get_user_by_id(user_id)
    
    if not user_data:
        return
    
    # Simple daily activity tracking (you might want to implement proper daily limits)
    #try:
        # This is a simplified version - in production you'd want proper daily tracking
        #if len(update.message.text or "") > 10:  # Only for meaningful messages
            #add_points_to_user(user_id, 1)
            
    #except Exception as e:
        #logger.error(f"Failed to award activity points: {e}")
