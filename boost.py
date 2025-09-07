from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
import uuid
from datetime import datetime
import html

from db import (
    get_user_by_id, add_points_to_user,
    deduct_points, save_promotion, add_booster, get_promotion
)
from utils import GROUP_ID, PROMOTE_TOPIC_ID

# Conversation states
BOOST_DESCRIPTION = 1
BOOST_SPECIAL_DESCRIPTION = 2

# =======================================================================
# FUNGSI UNTUK BOOST STANDAR (/boost)
# =======================================================================
async def boost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /boost command - meminta link terlebih dahulu."""
    if update.message.chat.type != "private":
        await update.message.reply_text("❌ Perintah ini hanya bisa digunakan via DM dengan bot.")
        return ConversationHandler.END
        
    user_id = str(update.effective_user.id)

    # 1. Pastikan pengguna sudah terdaftar dan memiliki poin yang cukup
    user_data = get_user_by_id(user_id)
    if not user_data:
        await update.message.reply_text("❌ Kamu harus terdaftar sebagai member untuk menggunakan fitur ini.")
        return ConversationHandler.END

    if user_data['points'] < 10:
        await update.message.reply_text(f"❌ Poin kamu ({user_data['points']}) tidak cukup. Butuh minimal 10 poin.")
        return ConversationHandler.END

    # 2. Ambil link dari input pengguna
    try:
        link = context.args[0]
        if not link.startswith(('http://', 'https://')):
            link = f"https://{link}"
        
        # Simpan data sementara di context
        context.user_data['boost_link'] = link
        context.user_data['boost_type'] = 'standar'
        context.user_data['boost_cost'] = 10
        
    except IndexError:
        await update.message.reply_text(
            "Silakan sertakan link. Contoh: <code>/boost https://instagram.com/namakamu</code>",
        parse_mode="HTML")
        return ConversationHandler.END

    # 3. Minta deskripsi action
    await update.message.reply_text(
        f"✅ Link diterima: {link}\n\n"
        f"📝 Sekarang jelaskan apa yang harus dilakukan member dengan link ini?\n\n"
        f"Contoh deskripsi:\n"
        f"• follow - untuk follow akun Instagram/Twitter\n"
        f"• like - untuk like postingan tertentu\n"
        f"• comment - untuk comment di postingan\n"
        f"• subscribe - untuk subscribe channel YouTube\n"
        f"• join - untuk join grup Telegram/Discord\n"
        f"• view - untuk view/watch video\n"
        f"• atau tulis deskripsi custom lainnya\n\n"
        f"💡 <b>Ketik deskripsi action yang diinginkan:</b>",
        parse_mode="HTML"
    )
    
    return BOOST_DESCRIPTION

async def boost_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deskripsi untuk boost standar"""
    user_id = str(update.effective_user.id)
    description = update.message.text.strip().lower()
    
    # Validasi deskripsi
    if len(description) > 50:
        await update.message.reply_text("❌ Deskripsi terlalu panjang. Maksimal 50 karakter.")
        return BOOST_DESCRIPTION
        
    if len(description) < 3:
        await update.message.reply_text("❌ Deskripsi terlalu pendek. Minimal 3 karakter.")
        return BOOST_DESCRIPTION
    
    # Ambil data dari context
    link = context.user_data['boost_link']
    boost_cost = context.user_data['boost_cost']
    
    # 4. Kurangi poin dan simpan boost ke database
    deduct_points(user_id, boost_cost)
    boost_id = str(uuid.uuid4())[:8]
    
    user_data = get_user_by_id(user_id)
    boost_data = {
        'promo_id': boost_id,
        'user_id': user_id,
        'link': link,
        'type': 'standar',
        'boosters': [],
        'description': description
    }
    save_promotion(boost_data)

    # Notifikasi ke user
    await update.message.reply_text(
        f"✅ Boost Anda telah dikonfirmasi. Saldo poin Anda dikurangi <b>{boost_cost} poin</b>.",
        parse_mode="HTML"
    )
    await update.message.reply_text(
        f"🎉 Selamat !!\n"
        f"Boost Anda berhasil diposting!\n"
        f"ID Boost: <code>{boost_id}</code>\n"
        f"Action: <b>{description}</b>\n"
        f"Gunakan ID ini untuk memeriksa booster dengan perintah:\n"
        f"<code>/cek_booster {boost_id}</code>\n"
        f"⚠️ Jika terdapat kecurangan, segera laporkan ke admin.",
        parse_mode="HTML"
    )

    # 5. Buat tombol dan pesan boost
    callback_data = f"boost:{boost_id}"
    keyboard = [[InlineKeyboardButton("Boost & Get 1 Point", callback_data=callback_data)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    safe_username = html.escape(user_data['username'])
    safe_description = html.escape(description.title())

    message_text = (
        f"🚀 <b>BOOST TIME!</b> 🚀\n\n"
        f"✨ @{safe_username} butuh bantuan untuk <b>{safe_description}</b> nih! 🎯\n"
        f"Yuk bantu sekarang, jangan cuma jadi penonton 😎\n\n"
        f"👇 Klik tombol, dapet poin, dapet pahala! ✨"
    )

    # 6. Kirim pesan ke grup
    sent_message = await context.bot.send_message(
        chat_id=GROUP_ID,
        message_thread_id=PROMOTE_TOPIC_ID,
        text=message_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    
    # 7. Jadwalkan auto-delete setelah 24 jam
    try:
        if context.job_queue:
            context.job_queue.run_once(
                delete_boost_message,
                when=24*60*60,  # 24 jam dalam detik
                data={"chat_id": GROUP_ID, "message_id": sent_message.message_id}
            )
    except Exception as e:
        print(f"Warning: Auto-delete scheduling failed: {e}")

    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

# =======================================================================
# FUNGSI UNTUK BOOST SPESIAL (/boost_special)
# =======================================================================
async def boost_special_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /boost_special command."""
    if update.message.chat.type != "private":
        await update.message.reply_text("❌ Perintah ini hanya bisa digunakan via DM dengan bot.")
        return ConversationHandler.END
    
    user_id = str(update.effective_user.id)

    # Pastikan pengguna terdaftar dan punya poin yang cukup (15 poin)
    user_data = get_user_by_id(user_id)
    if not user_data:
        await update.message.reply_text("❌ Kamu harus terdaftar sebagai member untuk menggunakan fitur ini.")
        return ConversationHandler.END

    if user_data['points'] < 15:
        await update.message.reply_text(f"❌ Poin kamu ({user_data['points']}) tidak cukup. Butuh minimal 15 poin.")
        return ConversationHandler.END

    # Ambil link dari input pengguna
    try:
        link = context.args[0]
        if not link.startswith(('http://', 'https://')):
            link = f"https://{link}"
            
        # Simpan data sementara di context
        context.user_data['boost_link'] = link
        context.user_data['boost_type'] = 'spesial'
        context.user_data['boost_cost'] = 15
        
    except IndexError:
        await update.message.reply_text(
            "Silakan sertakan link. Contoh: /boost_special https://instagram.com/namakamu"
        )
        return ConversationHandler.END

    # Minta deskripsi action
    await update.message.reply_text(
        f"✅ Link diterima: {link}\n\n"
        f"📝 Sekarang jelaskan apa yang harus dilakukan member dengan link ini?\n\n"
        f"Contoh deskripsi:\n"
        f"• follow - untuk follow akun Instagram/Twitter\n"
        f"• like - untuk like postingan tertentu\n"
        f"• comment - untuk comment di postingan\n"
        f"• subscribe - untuk subscribe channel YouTube\n"
        f"• join - untuk join grup Telegram/Discord\n"
        f"• view - untuk view/watch video\n"
        f"• atau tulis deskripsi custom lainnya\n\n"
        f"💡 <b>Ketik deskripsi action yang diinginkan:</b>",
        parse_mode="HTML"
    )
    
    return BOOST_SPECIAL_DESCRIPTION

async def boost_special_description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deskripsi untuk boost spesial"""
    user_id = str(update.effective_user.id)
    description = update.message.text.strip().lower()
    
    # Validasi deskripsi
    if len(description) > 50:
        await update.message.reply_text("❌ Deskripsi terlalu panjang. Maksimal 50 karakter.")
        return BOOST_SPECIAL_DESCRIPTION
        
    if len(description) < 3:
        await update.message.reply_text("❌ Deskripsi terlalu pendek. Minimal 3 karakter.")
        return BOOST_SPECIAL_DESCRIPTION
    
    # Ambil data dari context
    link = context.user_data['boost_link']
    boost_cost = context.user_data['boost_cost']

    # Kurangi poin dan simpan boost ke database
    deduct_points(user_id, boost_cost)
    boost_id = str(uuid.uuid4())[:8]
    
    user_data = get_user_by_id(user_id)
    boost_data = {
        'promo_id': boost_id,
        'user_id': user_id,
        'link': link,
        'type': 'spesial',
        'boosters': [],
        'description': description
    }
    save_promotion(boost_data)

    # ✅ Notifikasi ke user
    await update.message.reply_text(
        f"✅ Boost Spesial Anda telah dikonfirmasi. Saldo poin Anda dikurangi <b>{boost_cost} poin</b>.",
        parse_mode="HTML"
    )
    await update.message.reply_text(
        f"🎉 Boost Spesial berhasil diposting!\n"
        f"ID Boost: <code>{boost_id}</code>\n"
        f"Action: <b>{description}</b>\n"
        f"Gunakan ID ini untuk memeriksa booster dengan perintah:\n"
        f"<code>/cek_booster {boost_id}</code>",
        parse_mode="HTML"
    )

    # Buat tombol dan pesan boost
    callback_data = f"boost:{boost_id}"
    keyboard = [[InlineKeyboardButton("Boost & Get 1 Point", callback_data=callback_data)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    safe_username = html.escape(user_data['username'])
    safe_description = html.escape(description.title())

    message_text = (
        "👑 <b>SPESIAL BOOST ALERT!</b> 👑\n\n"
        f"Hari ini giliran <b>@{safe_username}</b> naik ke spotlight untuk <b>{safe_description}</b> ✨\n"
        "🚀 Bantu dia makin grow & dapetin vibes komunitas!\n\n"
        "🎁 Bonus: +1 poin buat kamu yang support lewat tombol di bawah!"
    )

    # Kirim pesan ke grup
    sent_message = await context.bot.send_message(
        chat_id=GROUP_ID,
        message_thread_id=PROMOTE_TOPIC_ID,
        text=message_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    # Pin pesan di grup
    await context.bot.pin_chat_message(
        chat_id=GROUP_ID,
        message_id=sent_message.message_id
    )

    # Jadwalkan auto-unpin 2 hari
    try:
        if context.job_queue:
            context.job_queue.run_once(
                unpin_message,
                when=2*24*60*60,  # 2 hari dalam detik
                data={"chat_id": GROUP_ID, "message_id": sent_message.message_id}
            )
    except Exception as e:
        print(f"Warning: Auto-unpin scheduling failed: {e}")
        
    # Info terakhir ke user
    await update.message.reply_text(
        "✅ Boost Spesial Anda telah berhasil diposting dan disematkan di grup."
    )

    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

# =======================================================================
# BUTTON HANDLER
# =======================================================================
async def boost_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all inline button callbacks."""
    query = update.callback_query
    print(f"✅ BOOST HANDLER: Button handler BERHASIL dipanggil!")
    print(f"✅ BOOST HANDLER: User {query.from_user.id} (@{query.from_user.username})")
    print(f"✅ BOOST HANDLER: Callback data: '{query.data}'")
    
    await query.answer()

    if query.data.startswith('boost:'):
        boost_id = query.data.split(':')[1]
        user_id = str(query.from_user.id)
        print(f"🔍 DEBUG: Processing boost button - boost_id: {boost_id}, user_id: {user_id}")

        # 1. Ambil data boost dari database
        boost_data = get_promotion(boost_id)
        if not boost_data:
            await query.answer("❌ Boost ini tidak ditemukan.")
            return

        # 2. Periksa apakah pengguna sudah pernah mengklik
        if user_id in boost_data['boosters']:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="⚠️ Anda sudah pernah mendapatkan poin dari boost ini. Klik Anda tidak dihitung lagi."
                )
            except Exception as e:
                print(f"Gagal mengirim DM ke pengguna {user_id}: {e}")
            await query.answer("Anda sudah pernah mendapatkan poin dari boost ini.")
            return

        # 3. Tambah poin dan catat interaksi
        add_points_to_user(user_id, 1)
        add_booster(boost_id, user_id)

        # 4. Kirim notifikasi DM
        print(f"🔍 DEBUG: Mencoba mengirim DM ke user_id: {user_id}")
        
        try:
            # Cek dulu apakah user sudah start bot
            try:
                test_message = await context.bot.send_chat_action(chat_id=user_id, action="typing")
                print(f"✅ DEBUG: User {user_id} bisa menerima DM")
            except Exception as test_e:
                print(f"❌ DEBUG: User {user_id} tidak bisa menerima DM: {test_e}")
                await query.answer("⚠️ Poin ditambahkan! Tapi Anda harus /start bot dulu untuk menerima DM link.", show_alert=True)
                return
            
            link = boost_data['link']
            description = boost_data.get('description', 'follow')
            
            # Pastikan link punya prefix
            if not link.startswith(("http://", "https://")):
                link = "https://" + link

            # Ambil data pemilik boost
            boost_owner = get_user_by_id(boost_data['user_id'])
            owner_username = boost_owner['username'] if boost_owner else "Unknown"

            # Pesan informasi (tanpa link)
            info_text = (
                f"🚀 <b>Terima kasih sudah support @{owner_username}!</b>\n\n"
                f"📋 <b>Yang harus dilakukan: {description.upper()}</b>\n\n"
                f"🪙 <b>+1 poin</b> telah ditambahkan ke akun Anda!\n"
                f"💰 Cek saldo poin dengan <code>/points</code>\n\n"
                f"💡 <b>Tips:</b> Pastikan lakukan action '{description}' untuk mendukung member komunitas!\n"
                f"⚠️ <b>Peringatan:</b> Jika ditemukan kecurangan, poin akan direset."
            )

            # Kirim pesan informasi terlebih dahulu
            await context.bot.send_message(
                chat_id=user_id,
                text=info_text,
                parse_mode="HTML"
            )
            
            # Kirim link sebagai pesan terpisah agar bisa diklik
            link_text = f"🔗 Link untuk {description}:\n{link}"
            dm_message = await context.bot.send_message(
                chat_id=user_id,
                text=link_text,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
            print(f"✅ DEBUG: DM berhasil dikirim ke user {user_id}")
            
            # 5. Kirim pop-up konfirmasi sukses
            await query.answer(f"✅ Poin berhasil ditambahkan. Silakan {description} dan cek DM untuk linknya!")
            
        except Exception as e:
            print(f"❌ DEBUG: Gagal mengirim DM ke pengguna {user_id}: {e}")
            
            if "Forbidden" in str(e) or "blocked" in str(e).lower():
                error_msg = "⚠️ Poin ditambahkan! Tapi Anda harus /start bot dulu untuk menerima DM link."
            elif "Chat not found" in str(e):
                error_msg = "⚠️ Poin ditambahkan! Tapi bot tidak bisa mengirim DM. Silakan /start bot terlebih dahulu."
            else:
                error_msg = "⚠️ Poin ditambahkan! Tapi DM gagal terkirim. Silakan hubungi admin untuk link."
            
            await query.answer(error_msg, show_alert=True)
            return

# =======================================================================
# UTILITY FUNCTIONS
# =======================================================================
async def delete_boost_message(context: ContextTypes.DEFAULT_TYPE):
    """Delete boost message after 24 hours"""
    job = context.job
    try:
        await context.bot.delete_message(
            chat_id=job.data["chat_id"],
            message_id=job.data["message_id"]
        )
    except Exception as e:
        print(f"Failed to delete boost message: {e}")

async def unpin_message(context: ContextTypes.DEFAULT_TYPE):
    """Unpin special boost message after specified time"""
    job = context.job
    try:
        await context.bot.unpin_chat_message(
            chat_id=job.data["chat_id"],
            message_id=job.data["message_id"]
        )
    except Exception as e:
        print(f"Failed to unpin message: {e}")

# =======================================================================
# CEK BOOSTER
# =======================================================================
async def cek_booster_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /cek_booster command."""
    user_id = str(update.effective_user.id)

    # 1. Pastikan pengguna memberikan ID boost
    try:
        boost_id = context.args[0]
    except IndexError:
        await update.message.reply_text("Silakan sertakan ID boost. Contoh: /cek_booster BOOST1234")
        return

    # 2. Ambil data boost dari database
    boost_data = get_promotion(boost_id)

    if not boost_data:
        await update.message.reply_text("❌ Boost dengan ID tersebut tidak ditemukan.")
        return

    # 3. Pastikan pengguna yang meminta adalah pemilik boost
    if str(boost_data['user_id']) != user_id:
        await update.message.reply_text("❌ Anda tidak memiliki izin untuk melihat data boost ini.")
        return

    # 4. Ambil daftar booster dan username mereka
    booster_ids = boost_data['boosters']
    booster_usernames = []
    description = boost_data.get('description', 'follow')

    for booster_id in booster_ids:
        booster_user_data = get_user_by_id(booster_id)
        if booster_user_data:
            booster_usernames.append(f"• @{booster_user_data['username']}")
        else:
            booster_usernames.append("• Pengguna tidak ditemukan")

    usernames_list = "\n".join(booster_usernames) if booster_usernames else "Belum ada yang boost"

    # 5. Kirim laporan
    report_text = (
        f"📊 <b>Laporan Booster {boost_id}</b>\n\n"
        f"📋 <b>Action:</b> {description.title()}\n"
        f"🔗 <b>Link:</b> {boost_data['link']}\n"
        f"📈 <b>Total boost:</b> {len(booster_ids)}\n\n"
        f"👥 <b>Daftar booster:</b>\n"
        f"{usernames_list}\n\n"
        f"💡 Silahkan cek kembali apakah jumlah {description} sudah sesuai dengan daftar booster di atas.\n"
        f"⚠️ Laporkan ke admin jika ada ketidaksesuaian."
    )

    await update.message.reply_text(
        report_text,
        parse_mode="HTML"
    )

# =======================================================================
# CANCEL HANDLER
# =======================================================================
async def cancel_boost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel boost conversation"""
    await update.message.reply_text(
        "❌ Boost dibatalkan. Gunakan /boost atau /boost_special untuk memulai lagi."
    )
    context.user_data.clear()
    return ConversationHandler.END