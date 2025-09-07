from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters, CommandHandler
)
from db import (
    add_user, get_user_by_id, get_user_by_username, add_points_to_user, 
    get_referrals_by_username, get_badges, add_badge_to_user, has_badge
)
from utils import validate_phone_number, sanitize_input, get_user_display_name

import logging

def log_activity(action_type, user_id, description):
    """Simple activity logging function"""
    logger.info(f"Activity: {action_type} - User: {user_id} - {description}")

logger = logging.getLogger(__name__)

# State constants
(
    USERNAME, REFERRAL, WHATSAPP, TELEGRAM, PAYMENT_METHOD, PAYMENT_NUMBER, OWNER_NAME,
    CHOOSE_FIELD, EDIT_USERNAME, EDIT_WHATSAPP, EDIT_TELEGRAM, EDIT_PAYMENT_METHOD, EDIT_PAYMENT_NUMBER, EDIT_OWNER_NAME
) = range(14)

# ========== REGISTER ==========

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start registration process"""
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "❌ *Pendaftaran Hanya via Private Chat*\n\n"
            "Untuk menjaga privasi data kamu, pendaftaran hanya bisa dilakukan melalui private chat.\n\n"
            "👉 Silakan buka DM ke bot lalu kirim `/register`",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    user_id = str(update.effective_user.id)
    if get_user_by_id(user_id):
        user_data = get_user_by_id(user_id)
        await update.message.reply_text(
            f"✅ *Kamu Sudah Terdaftar!*\n\n"
            f"👤 Username: `{user_data['username']}`\n"
            f"💰 Points: {user_data.get('points', 0)}\n\n"
            "Gunakan `/editinfo` untuk mengubah data atau `/myinfo` untuk melihat detail lengkap.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    user_display = get_user_display_name(update.effective_user)
    await update.message.reply_text(
        f"✨ *Selamat Datang {user_display}!*\n\n"
        "Yuk kita mulai proses pendaftaran member NexoBuzz!\n\n"
        "📌 *Langkah 1/7: Username*\n"
        "👤 Buat username yang unik dan mudah diingat!\n\n"
        "💡 *Tips:*\n"
        "• Username akan digunakan untuk identifikasi di setiap job\n"
        "• Gunakan huruf, angka, dan underscore saja\n"
        "• Disarankan sama dengan username Telegram kamu\n\n"
        "Ketik username yang kamu inginkan:",
        parse_mode="Markdown"
    )
    return USERNAME

async def username_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle username input"""
    username = sanitize_input(update.message.text.strip())
    
    # Validation
    if len(username) < 3:
        await update.message.reply_text("❌ Username minimal 3 karakter. Coba lagi:")
        return USERNAME
    
    if len(username) > 20:
        await update.message.reply_text("❌ Username maksimal 20 karakter. Coba lagi:")
        return USERNAME
    
    if not username.replace('_', '').replace('-', '').isalnum():
        await update.message.reply_text("❌ Username hanya boleh mengandung huruf, angka, underscore (_), dan strip (-). Coba lagi:")
        return USERNAME
    
    if get_user_by_username(username):
        await update.message.reply_text(
            f"❌ Username `{username}` sudah dipakai member lain.\n\n"
            "Silakan pilih username lain yang unik!",
            parse_mode="Markdown"
        )
        return USERNAME
    
    context.user_data['username'] = username
    await update.message.reply_text(
        "📌 *Langkah 2/7: Kode Referral*\n"
        "🔗 Masukkan username teman yang mengajak kamu bergabung\n\n"
        "💰 *Benefit Referral:*\n"
        "• Referrer mendapat +25 poin\n"
        "• Kamu mendapat bonus poin awal\n\n"
        "Ketik username referrer atau *_Skip_* jika tidak ada:",
        parse_mode="Markdown"
    )
    return REFERRAL

async def referral_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle referral input"""
    ref = sanitize_input(update.message.text.strip())
    
    if ref.lower() == "skip":
        context.user_data['referrer'] = None
        context.user_data['referrer_user_id'] = None
    else:
        ref_user = get_user_by_username(ref)
        if not ref_user:
            await update.message.reply_text(
                f"❌ Username referral `{ref}` tidak ditemukan.\n\n"
                "Ketik username yang valid atau `Skip` untuk melewati:",
                parse_mode="Markdown"
            )
            return REFERRAL
        
        # Don't allow self-referral
        if ref_user['user_id'] == str(update.effective_user.id):
            await update.message.reply_text("❌ Kamu tidak bisa mereferensikan diri sendiri! Ketik username lain atau `Skip`:")
            return REFERRAL
            
        context.user_data['referrer'] = ref_user['username']
        context.user_data['referrer_user_id'] = ref_user['user_id']
    
    await update.message.reply_text(
        "📌 *Langkah 3/7: Nomor WhatsApp*\n"
        "☎️ Masukkan nomor WhatsApp kamu\n\n"
        "📝 *Format yang diterima:*\n"
        "• 08xxxxxxxxxx\n"
        "• +62xxxxxxxxx\n"
        "• 62xxxxxxxxx\n\n"
        "Ketik nomor WhatsApp kamu:",
        parse_mode="Markdown"
    )
    return WHATSAPP

async def whatsapp_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle WhatsApp number input"""
    whatsapp = sanitize_input(update.message.text.strip())
    validated_phone = validate_phone_number(whatsapp)
    
    if not validated_phone:
        await update.message.reply_text(
            "❌ *Format nomor tidak valid!*\n\n"
            "Gunakan format yang benar:\n"
            "• 08xxxxxxxxxx\n"
            "• +62xxxxxxxxx\n"
            "• 62xxxxxxxxx\n\n"
            "Coba lagi:",
            parse_mode="Markdown"
        )
        return WHATSAPP
    
    context.user_data['whatsapp'] = validated_phone
    await update.message.reply_text(
        "📌 *Langkah 4/7: Nomor Telegram*\n"
        "📱 Masukkan nomor Telegram kamu\n\n"
        "💡 Jika nomor Telegram sama dengan WhatsApp, ketik `Skip`\n\n"
        "Ketik nomor Telegram kamu:",
        parse_mode="Markdown"
    )
    return TELEGRAM

async def telegram_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Telegram number input"""
    val = sanitize_input(update.message.text.strip())
    
    if val.lower() == "skip":
        context.user_data['telegram'] = context.user_data['whatsapp']
    else:
        validated_phone = validate_phone_number(val)
        if not validated_phone:
            await update.message.reply_text(
                "❌ *Format nomor tidak valid!*\n\n"
                "Gunakan format yang benar atau ketik `Skip` jika sama dengan WhatsApp:\n\n"
                "Coba lagi:",
                parse_mode="Markdown"
            )
            return TELEGRAM
        context.user_data['telegram'] = validated_phone
    
    keyboard = [
        [
            InlineKeyboardButton("💳 Dana", callback_data="Dana"),
            InlineKeyboardButton("🏦 Seabank", callback_data="Seabank")
        ],
    ]
    
    await update.message.reply_text(
        "📌 *Langkah 5/7: Metode Payment*\n"
        "💳 Pilih metode pembayaran untuk menerima fee job\n\n"
        "Pilih salah satu:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PAYMENT_METHOD

async def payment_method_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['payment_method'] = query.data
    await query.edit_message_text(
        f"📌 *Langkah 6/7: Nomor Payment*\n"
        f"🔢 Masukkan nomor {query.data} kamu\n\n"
        f"⚠️ Pastikan nomor yang kamu masukkan benar dan aktif!",
        parse_mode="Markdown"
    )
    return PAYMENT_NUMBER

async def payment_number_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment number input"""
    payment_number = sanitize_input(update.message.text.strip())
    
    if len(payment_number) < 8:
        await update.message.reply_text("❌ Nomor payment terlalu pendek. Masukkan nomor yang valid:")
        return PAYMENT_NUMBER
    
    context.user_data['payment_number'] = payment_number
    await update.message.reply_text(
        "📌 *Langkah 7/7: Nama Pemilik*\n"
        "📝 Masukkan nama pemilik rekening/e-wallet\n\n"
        "💡 Nama ini harus sesuai dengan yang terdaftar di akun payment kamu!\n\n"
        "Ketik nama lengkap:",
        parse_mode="Markdown"
    )
    return OWNER_NAME

async def owner_name_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle owner name input and complete registration"""
    owner_name = sanitize_input(update.message.text.strip())
    
    if len(owner_name) < 2:
        await update.message.reply_text("❌ Nama terlalu pendek. Masukkan nama lengkap:")
        return OWNER_NAME
    
    user_id = str(update.effective_user.id)
    context.user_data['owner_name'] = owner_name
    context.user_data['points'] = 5  # Welcome bonus

    # Save user to database
    try:
        add_user(user_id, context.user_data)
        data = get_user_by_id(user_id)
        
        # Process referral if exists
        referrer_user_id = context.user_data.get('referrer_user_id')
        referrer_username = context.user_data.get('referrer')
        
        if referrer_user_id and referrer_username:
            try:
                # Give points to referrer
                add_points_to_user(referrer_user_id, 25)
                
                # Give extra welcome bonus to new user
                add_points_to_user(user_id, 10)  # Total 25 points for referred users
                
                # Notify referrer
                try:
                    referral_count = len(get_referrals_by_username(referrer_username))
                    await context.bot.send_message(
                        chat_id=referrer_user_id,
                        text=(
                            f"🎉 *Referral Berhasil!*\n\n"
                            f"👤 `{data['username']}` berhasil daftar dengan kode referral kamu!\n\n"
                            f"💰 *Reward:*\n"
                            f"• +25 poin ditambahkan ke akun kamu\n"
                            f"• Total referral kamu: {referral_count} orang\n\n"
                            f"Terima kasih sudah membantu mengembangkan komunitas NexoBuzz! 🚀"
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify referrer: {e}")
                    
            except Exception as e:
                logger.error(f"Failed to process referral: {e}")

        # Add welcome badge
        if not has_badge(user_id, "🌟 New Member"):
            add_badge_to_user(user_id, "🌟 New Member")

        # Log activity
        log_activity("registration", user_id, f"New member registered: {data['username']}")

        # Success message
        total_points = 10 if referrer_user_id else 5
        summary = (
            "🎉 *Pendaftaran Berhasil!*\n\n"
            f"👤 *Username:* `{data['username']}`\n"
            f"☎️ *WhatsApp:* `{data['whatsapp']}`\n"
            f"📱 *Telegram:* `{data['telegram']}`\n"
            f"💳 *Payment:* {data['payment_method']}\n"
            f"🔢 *Nomor:* `{data['payment_number']}`\n"
            f"📝 *A/n:* {data['owner_name']}\n"
            f"🔗 *Referrer:* {data.get('referrer', 'Tidak ada')}\n"
            f"💰 *Welcome Bonus:* {total_points} poin\n\n"
            "✅ *Akun kamu sudah aktif!*\n\n"
            "📋 *Langkah Selanjutnya:*\n"
            "• Ketik /start 👉 Join Group\n"
            "• Gunakan /listjob untuk melihat job tersedia\n"
            "• Gunakan /help untuk panduan lengkap\n\n"
            "Selamat bergabung di NexoBuzz! 🚀"
        )
        
        await update.message.reply_text(summary, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Registration failed for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ *Pendaftaran Gagal*\n\n"
            "Terjadi kesalahan saat menyimpan data. Silakan coba lagi nanti atau hubungi admin.",
            parse_mode="Markdown"
        )
        
    context.user_data.clear()
    return ConversationHandler.END

# ========== EDITINFO ==========

async def editinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start edit info process"""
    user_id = str(update.effective_user.id)
    data = get_user_by_id(user_id)
    
    if not data:
        await update.message.reply_text(
            "❌ *Kamu Belum Terdaftar*\n\n"
            "Gunakan `/register` untuk mendaftar sebagai member terlebih dahulu.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("👤 Username", callback_data="edit_username")],
        [InlineKeyboardButton("☎️ WhatsApp", callback_data="edit_whatsapp")],
        [InlineKeyboardButton("📱 Telegram", callback_data="edit_telegram")],
        [InlineKeyboardButton("💳 Metode Payment", callback_data="edit_payment_method")],
        [InlineKeyboardButton("🔢 Nomor Payment", callback_data="edit_payment_number")],
        [InlineKeyboardButton("📝 Nama Pemilik", callback_data="edit_owner_name")],
        [InlineKeyboardButton("❌ Cancel", callback_data="edit_cancel")],
    ]
    
    await update.message.reply_text(
        "⚙️ *Edit Informasi Member*\n\n"
        "Pilih data yang ingin kamu ubah:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CHOOSE_FIELD

async def choose_field_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field selection for editing"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "edit_username":
        await query.edit_message_text(
            "👤 *Edit Username*\n\n"
            "Masukkan username baru:\n\n"
            "💡 *Catatan:* Username harus unik dan tidak digunakan member lain.",
            parse_mode="Markdown"
        )
        return EDIT_USERNAME
        
    elif query.data == "edit_whatsapp":
        await query.edit_message_text(
            "☎️ *Edit Nomor WhatsApp*\n\n"
            "Masukkan nomor WhatsApp baru:",
            parse_mode="Markdown"
        )
        return EDIT_WHATSAPP
        
    elif query.data == "edit_telegram":
        await query.edit_message_text(
            "📱 *Edit Nomor Telegram*\n\n"
            "Masukkan nomor Telegram baru:",
            parse_mode="Markdown"
        )
        return EDIT_TELEGRAM
        
    elif query.data == "edit_payment_method":
        keyboard = [
            [InlineKeyboardButton("💳 Dana", callback_data="Dana")],
            [InlineKeyboardButton("🏦 Seabank", callback_data="Seabank")]
        ]
        await query.edit_message_text(
            "💳 <b>Edit Metode Payment</b>\n\n"
            "Pilih metode pembayaran baru:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return EDIT_PAYMENT_METHOD
        
    elif query.data == "edit_payment_number":
        await query.edit_message_text(
            "🔢 *Edit Nomor Payment*\n\n"
            "Masukkan nomor payment baru:",
            parse_mode="Markdown"
        )
        return EDIT_PAYMENT_NUMBER
        
    elif query.data == "edit_owner_name":
        await query.edit_message_text(
            "📝 *Edit Nama Pemilik*\n\n"
            "Masukkan nama pemilik rekening/e-wallet baru:",
            parse_mode="Markdown"
        )
        return EDIT_OWNER_NAME
        
    elif query.data == "edit_cancel":
        await query.edit_message_text(
            "‼️ *Pengeditan di batalkan*\n\n"
            "tidak ada data yang di ubah!\n\n"
            "Gunakan `/myinfo` untuk melihat data terbaru.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

async def edit_username_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle username edit"""
    new_username = sanitize_input(update.message.text.strip())
    user_id = str(update.effective_user.id)

    # Validation
    if len(new_username) < 3:
        await update.message.reply_text("❌ Username minimal 3 karakter. Coba lagi:")
        return EDIT_USERNAME

    if get_user_by_username(new_username):
        await update.message.reply_text("❌ Username sudah dipakai member lain. Pilih yang lain:")
        return EDIT_USERNAME

    data = get_user_by_id(user_id)
    old_username = data['username']
    data['username'] = new_username
    add_user(user_id, data)

    log_activity("edit_info", user_id, f"Username changed from {old_username} to {new_username}")

    await update.message.reply_text(
        f"✅ *Username Berhasil Diubah*\n\n"
        f"Username baru: `{new_username}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def edit_whatsapp_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle WhatsApp edit"""
    new_whatsapp = sanitize_input(update.message.text.strip())
    validated_phone = validate_phone_number(new_whatsapp)

    if not validated_phone:
        await update.message.reply_text("❌ Format nomor tidak valid. Coba lagi:")
        return EDIT_WHATSAPP

    user_id = str(update.effective_user.id)
    data = get_user_by_id(user_id)
    data['whatsapp'] = validated_phone
    add_user(user_id, data)

    log_activity("edit_info", user_id, "WhatsApp number updated")

    await update.message.reply_text(
        f"✅ *Nomor WhatsApp Berhasil Diubah*\n\n"
        f"Nomor baru: `{validated_phone}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def edit_telegram_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Telegram edit"""
    new_telegram = sanitize_input(update.message.text.strip())
    validated_phone = validate_phone_number(new_telegram)

    if not validated_phone:
        await update.message.reply_text("❌ Format nomor tidak valid. Coba lagi:")
        return EDIT_TELEGRAM

    user_id = str(update.effective_user.id)
    data = get_user_by_id(user_id)
    data['telegram'] = validated_phone
    add_user(user_id, data)

    log_activity("edit_info", user_id, "Telegram number updated")

    await update.message.reply_text(
        f"✅ *Nomor Telegram Berhasil Diubah*\n\n"
        f"Nomor baru: `{validated_phone}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def edit_payment_method_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method edit"""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = get_user_by_id(user_id)
    old_method = data['payment_method']
    data['payment_method'] = query.data
    add_user(user_id, data)

    log_activity("edit_info", user_id, f"Payment method changed from {old_method} to {query.data}")

    await query.edit_message_text(
        f"✅ *Metode Payment Berhasil Diubah*\n\n"
        f"Metode baru: {query.data}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def edit_payment_number_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment number edit"""
    new_payment_number = sanitize_input(update.message.text.strip())

    if len(new_payment_number) < 8:
        await update.message.reply_text("❌ Nomor payment terlalu pendek. Coba lagi:")
        return EDIT_PAYMENT_NUMBER

    user_id = str(update.effective_user.id)
    data = get_user_by_id(user_id)
    data['payment_number'] = new_payment_number
    add_user(user_id, data)

    log_activity("edit_info", user_id, "Payment number updated")

    await update.message.reply_text(
        f"✅ *Nomor Payment Berhasil Diubah*\n\n"
        f"Nomor baru: `{new_payment_number}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def edit_owner_name_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle owner name edit"""
    new_owner_name = sanitize_input(update.message.text.strip())

    if len(new_owner_name) < 2:
        await update.message.reply_text("❌ Nama terlalu pendek. Coba lagi:")
        return EDIT_OWNER_NAME

    user_id = str(update.effective_user.id)
    data = get_user_by_id(user_id)
    data['owner_name'] = new_owner_name
    add_user(user_id, data)

    log_activity("edit_info", user_id, "Owner name updated")

    await update.message.reply_text(
        f"✅ *Nama Pemilik Berhasil Diubah*\n\n"
        f"Nama baru: {new_owner_name}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ========== MYINFO COMMANDS ==========
async def myinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user information"""
    user_id = str(update.effective_user.id)
    data = get_user_by_id(user_id)

    if not data:
        await update.message.reply_text(
            "❌ <b>Kamu Belum Terdaftar</b>\n\n"
            "Gunakan <code>/register</code> untuk mendaftar sebagai member.",
            parse_mode="HTML"
        )
        return

    points = data.get('points', 0)
    referrer = data.get('referrer', 'Tidak ada')
    badges = get_badges(user_id)
    badge_text = " | ".join(badges) if badges else "Belum ada"

    # Get referral statistics
    referrals = get_referrals_by_username(data['username'])
    referral_count = len(referrals)

    summary = (
        "👤 <b>Profil Member</b>\n\n"
        f"👤 <b>Username:</b> <code>{data['username']}</code>\n"
        f"🏅 <b>Badge:</b> {badge_text}\n"
        f"💰 <b>Points:</b> {points}\n"
        f"👥 <b>Referrals:</b> {referral_count} orang\n"
        f"🔗 <b>Direferensi oleh:</b> {referrer}\n\n"
        "📞 <b>Kontak:</b>\n"
        f"☎️ WhatsApp: <code>{data['whatsapp']}</code>\n"
        f"📱 Telegram: <code>{data['telegram']}</code>\n\n"
        "💳 <b>Payment Info:</b>\n"
        f"💳 Metode: {data['payment_method']}\n"
        f"🔢 Nomor: <code>{data['payment_number']}</code>\n"
        f"📝 A/n: {data['owner_name']}\n\n"
        "⚙️ Gunakan <code>/editinfo</code> untuk mengubah data"
    )

    await update.message.reply_text(summary, parse_mode="HTML")

#============MY REFERRAL============
async def myreferral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's referral information"""
    user_id = str(update.effective_user.id)
    data = get_user_by_id(user_id)
    
    if not data:
        await update.message.reply_text(
            "❌ *Kamu Belum Terdaftar*\n\n"
            "Gunakan `/register` untuk mendaftar sebagai member.",
            parse_mode="Markdown"
        )
        return

    username = data['username']
    referrals = get_referrals_by_username(username)
    referral_count = len(referrals)
    total_referral_points = referral_count * 25
    
    text = (
        "👥 *Informasi Referral*\n\n"
        f"🆔 **Kode Referral Kamu:** `{username}`\n"
        f"👥 **Total Referral:** {referral_count} orang\n"
        f"💰 **Poin dari Referral:** {total_referral_points} poin\n\n"
        "📋 *Cara Menggunakan:*\n"
        "• Bagikan username kamu ke teman\n"
        "• Mereka daftar dengan kode referral kamu\n"
        "• Kamu dapat +25 poin setiap referral berhasil\n\n"
    )
    
    if referrals:
        text += "👥 *Daftar Referral:*\n"
        for i, ref in enumerate(referrals[:10], 1):  # Show max 10
            ref_points = ref.get('points', 0)
            text += f"{i}. {ref['username']} ({ref_points} poin)\n"
        
        if len(referrals) > 10:
            text += f"\n... dan {len(referrals) - 10} lainnya"
    else:
        text += "Belum ada yang menggunakan kode referral kamu. Yuk ajak teman-teman!"
    
    await update.message.reply_text(text, parse_mode="Markdown")
