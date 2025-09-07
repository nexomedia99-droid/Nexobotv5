from telegram import Update
from telegram.ext import ContextTypes
from decorators import admin_only
from db import (
    get_all_users, get_user_by_username, delete_user_by_id, add_points_to_user,
    add_badge_to_user, get_badges, get_conn
)
from utils import sanitize_input, get_user_display_name
import logging, re

logger = logging.getLogger(__name__)

@admin_only
async def listmember_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all registered members"""
    try:
        users = get_all_users()
        
        if not users:
            await update.message.reply_text("📭 Belum ada member yang terdaftar.")
            return
        
        # Split into chunks of 20 for better readability
        chunk_size = 20
        total_chunks = (len(users) + chunk_size - 1) // chunk_size
        
        page = 1
        if context.args and context.args[0].isdigit():
            page = max(1, min(int(context.args[0]), total_chunks))
        
        start_idx = (page - 1) * chunk_size
        end_idx = min(start_idx + chunk_size, len(users))
        
        text = f"👥 *Daftar Member* (Page {page}/{total_chunks})\n"
        text += f"Total: {len(users)} member\n\n"
        
        for i, user in enumerate(users[start_idx:end_idx], start=start_idx + 1):
            points = user.get('points', 0)
            text += f"{i}. `{user['username']}` - {points} poin\n"
        
        if total_chunks > 1:
            text += f"\n📄 Gunakan `/listmember <page>` untuk halaman lain"
        
        await update.message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Failed to list members: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mengambil daftar member.")

@admin_only
async def memberinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get detailed member information"""
    if not context.args:
        await update.message.reply_text(
            "📋 *Penggunaan:*\n"
            "`/memberinfo <username1> <username2> ...`\n"
            "`/memberinfo all` - Info semua member",
            parse_mode="Markdown"
        )
        return
    
    try:
        if context.args[0].lower() == "all":
            users = get_all_users()
            if not users:
                await update.message.reply_text("📭 Belum ada member yang terdaftar.")
                return
            
            # Limit to first 10 for "all"
            users = users[:10]
            text = f"👥 *Info Semua Member* (10 pertama)\n\n"
        else:
            usernames = [sanitize_input(arg) for arg in context.args]
            users = []
            not_found = []
            
            for username in usernames:
                user = get_user_by_username(username)
                if user:
                    users.append(user)
                else:
                    not_found.append(username)
            
            if not_found:
                await update.message.reply_text(
                    f"❌ Username tidak ditemukan: {', '.join(not_found)}"
                )
                return
            
            text = f"👤 *Info Member*\n\n"
        
        for i, user in enumerate(users, 1):
            badges = get_badges(user['user_id'])
            badge_text = " | ".join(badges) if badges else "Belum ada"
            
            text += (
                f"**{i}. {user['username']}**\n"
                f"🆔 ID: `{user['user_id']}`\n"
                f"🏅 Badge: {badge_text}\n"
                f"💰 Points: {user.get('points', 0)}\n"
                f"☎️ WhatsApp: `{user['whatsapp']}`\n"
                f"📱 Telegram: `{user['telegram']}`\n"
                f"🔗 Referrer: {user.get('referrer', 'Tidak ada')}\n\n"
            )
        
        # Split message if too long
        if len(text) > 4000:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
            
    except Exception as e:
        logger.error(f"Failed to get member info: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mengambil info member.")

#==========PAYMENT INFO===========
@admin_only
async def paymentinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get payment information for members"""
    if not context.args:
        await update.message.reply_text(
            "💳 <b>Penggunaan:</b>\n"
            "<code>/paymentinfo &lt;username1&gt; &lt;username2&gt; ...</code>\n"
            "atau:\n"
            "<code>/paymentinfo\\nuser1\\nuser2\\nuser3</code>",
            parse_mode="HTML"
        )
        return

    try:
        # Gabungkan semua argumen menjadi satu string
        raw_text = " ".join(context.args)

        # Split per baris, hapus angka/titik, dan strip spasi
        usernames = []
        for line in raw_text.splitlines():
            cleaned = re.sub(r'^\d+\.\s*', '', line).strip()  # hapus "1. " dkk
            if cleaned:
                usernames.append(sanitize_input(cleaned))

        users = []
        not_found = []

        for username in usernames:
            user = get_user_by_username(username)
            if user:
                users.append(user)
            else:
                not_found.append(username)

        if not_found:
            await update.message.reply_text(
                f"❌ Username tidak ditemukan: {', '.join(not_found)}"
            )
            return

        text = "💳 <b>Info Payment Member</b>\n\n"

        for i, user in enumerate(users, 1):
            whatsapp = user.get('whatsapp', '-')
            method = user.get('payment_method', '-')
            number = user.get('payment_number', '-')
            owner = user.get('owner_name', '-')

            text += (
                f"<b>{i}. {user['username']}</b>\n"
                f"💳 Metode: {method}\n"
                f"🔢 Nomor: <code>{number}</code>\n"
                f"📝 A/n: {owner}\n"
                f"☎️ WhatsApp: <code>{whatsapp}</code>\n\n"
            )

        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Failed to get payment info: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mengambil info payment.")


#=====DELETE MEMBER=====
@admin_only
async def delete_member_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete members from database"""
    if not context.args:
        await update.message.reply_text(
            "🗑️ *Penggunaan:*\n"
            "`/delete <username1> <username2> ...`",
            parse_mode="Markdown"
        )
        return
    
    try:
        usernames = [sanitize_input(arg) for arg in context.args]
        deleted = []
        not_found = []
        
        for username in usernames:
            user = get_user_by_username(username)
            if user:
                delete_user_by_id(user['user_id'])
                deleted.append(username)
      
            else:
                not_found.append(username)
        
        result_text = ""
        if deleted:
            result_text += f"✅ Berhasil menghapus: {', '.join(deleted)}\n"
        if not_found:
            result_text += f"❌ Tidak ditemukan: {', '.join(not_found)}"
        
        await update.message.reply_text(result_text)
        
    except Exception as e:
        logger.error(f"Failed to delete members: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat menghapus member.")

@admin_only
async def resetpoint_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset member points to 0"""
    if not context.args:
        await update.message.reply_text(
            "🔄 *Penggunaan:*\n"
            "`/resetpoint <username1> <username2> ...`",
            parse_mode="Markdown"
        )
        return
    
    try:
        usernames = [sanitize_input(arg) for arg in context.args]
        reset = []
        not_found = []
        
        for username in usernames:
            user = get_user_by_username(username)
            if user:
                # Reset points by setting to 0
                with get_conn() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE users SET points = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                        (user['user_id'],)
                    )
                    conn.commit()
                
                reset.append(username)
   
            else:
                not_found.append(username)
        
        result_text = ""
        if reset:
            result_text += f"✅ Points direset untuk: {', '.join(reset)}\n"
        if not_found:
            result_text += f"❌ Tidak ditemukan: {', '.join(not_found)}"
        
        await update.message.reply_text(result_text)
        
    except Exception as e:
        logger.error(f"Failed to reset points: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mereset points.")

@admin_only
async def addbadge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add badge to member"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "🏅 *Penggunaan:*\n"
            "`/addbadge <username> <badge_name>`\n\n"
            "*Contoh Badge:*\n"
            "🌟 New Member\n"
            "🎯 Member Aktif\n"
            "💼 Worker Pro\n"
            "🏆 Top Contributor\n"
            "🚀 Rising Star\n"
            "🔥 Fast Responder",
            parse_mode="Markdown"
        )
        return
    
    try:
        username = sanitize_input(context.args[0])
        badge_name = sanitize_input(" ".join(context.args[1:]))
        
        user = get_user_by_username(username)
        if not user:
            await update.message.reply_text(f"❌ Username `{username}` tidak ditemukan.", parse_mode="Markdown")
            return
        
        # Check if user already has the badge
        existing_badges = get_badges(user['user_id'])
        if badge_name in existing_badges:
            await update.message.reply_text(f"⚠️ `{username}` sudah memiliki badge `{badge_name}`", parse_mode="Markdown")
            return
        
        add_badge_to_user(user['user_id'], badge_name)
        
        await update.message.reply_text(
            f"✅ Badge `{badge_name}` berhasil ditambahkan ke `{username}`",
            parse_mode="Markdown"
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"🎉 Selamat! Kamu mendapat badge baru: *{badge_name}*",
                parse_mode="Markdown"
            )
        except:
            pass  # User might have blocked bot
        
    
        
    except Exception as e:
        logger.error(f"Failed to add badge: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat menambahkan badge.")

@admin_only
async def resetapply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset job applications for specific user or all"""
    if not context.args:
        await update.message.reply_text(
            "🔄 *Penggunaan:*\n"
            "`/resetapply <username>` - Reset apply user tertentu\n"
            "`/resetapply all` - Reset semua apply",
            parse_mode="Markdown"
        )
        return
    
    try:
        if context.args[0].lower() == "all":
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM applicants")
                conn.commit()
            
            await update.message.reply_text("✅ Semua aplikasi job telah direset.")
    
            
        else:
            username = sanitize_input(context.args[0])
            user = get_user_by_username(username)
            
            if not user:
                await update.message.reply_text(f"❌ Username `{username}` tidak ditemukan.", parse_mode="Markdown")
                return
            
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM applicants WHERE user_id = ?", (user['user_id'],))
                conn.commit()
            
            await update.message.reply_text(f"✅ Aplikasi job untuk `{username}` telah direset.", parse_mode="Markdown")
      
        
    except Exception as e:
        logger.error(f"Failed to reset applications: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mereset aplikasi.")

@admin_only
async def resetbadge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset badges for specific user or all"""
    if not context.args:
        await update.message.reply_text(
            "🔄 *Penggunaan:*\n"
            "`/resetbadge <username>` - Reset badge user tertentu\n"
            "`/resetbadge all` - Reset semua badge",
            parse_mode="Markdown"
        )
        return
    
    try:
        if context.args[0].lower() == "all":
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM achievements")
                conn.commit()
            
            await update.message.reply_text("✅ Semua badge telah direset.")
      
            
        else:
            username = sanitize_input(context.args[0])
            user = get_user_by_username(username)
            
            if not user:
                await update.message.reply_text(f"❌ Username `{username}` tidak ditemukan.", parse_mode="Markdown")
                return
            
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM achievements WHERE user_id = ?", (user['user_id'],))
                conn.commit()
            
            await update.message.reply_text(f"✅ Badge untuk `{username}` telah direset.", parse_mode="Markdown")
        
        
    except Exception as e:
        logger.error(f"Failed to reset badges: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mereset badge.")


#=========ADD POINTS=========
@admin_only
async def addpoint_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tambah poin manual ke banyak user.
    Format yang didukung:
    1) /addpoint | <jumlah> | <username1> <username2> ...
    2) /addpoint <jumlah> <username1> <username2> ...
    Username bisa dipisah dengan spasi, baris baru, atau diberi nomor urut (1. user1).
    """
    text = (update.message.text or "").strip()

    # Hilangkan '/addpoint' dari awal agar parsing lebih mudah
    after_cmd = ""
    parts = text.split(maxsplit=1)
    if len(parts) == 2:
        after_cmd = parts[1].strip()

    amount_str = None
    usernames_raw = ""

    # Mode dengan pipa: /addpoint | 10 | user1 user2
    if "|" in after_cmd:
        pipe_parts = [p.strip() for p in after_cmd.split("|") if p.strip()]
        if len(pipe_parts) < 2:
            return await update.message.reply_text(
                "❌ Format salah.\nContoh: `/addpoint | 25 | user1 user2`",
                parse_mode="Markdown"
            )
        amount_str = pipe_parts[0]
        usernames_raw = " ".join(pipe_parts[1:]).strip()
    else:
        # Mode tanpa pipa: /addpoint 10 user1 user2
        args = after_cmd.split()
        if len(args) < 2:
            return await update.message.reply_text(
                "🔧 *Penggunaan:*\n"
                "`/addpoint | <jumlah> | <username1> <username2> ...`\n"
                "atau\n"
                "`/addpoint <jumlah> <username1> <username2> ...`",
                parse_mode="Markdown"
            )
        amount_str = args[0]
        usernames_raw = " ".join(args[1:])

    # Validasi jumlah poin
    try:
        amount = int(amount_str)
        if amount <= 0:
            return await update.message.reply_text("❌ Jumlah poin harus lebih dari 0.")
    except ValueError:
        return await update.message.reply_text("❌ Jumlah poin harus berupa angka bulat.")

    # Kumpulkan username unik
    usernames = []
    seen = set()
    for raw in usernames_raw.split():
        # Buang format angka di depan (contoh: "1.", "2)")
        cleaned = re.sub(r'^\d+[\.\)]*', '', raw).strip()
        su = sanitize_input(cleaned)
        if su and su not in seen:
            seen.add(su)
            usernames.append(su)

    if not usernames:
        return await update.message.reply_text("❌ Harus mencantumkan minimal 1 username.")

    updated, not_found, failed = [], [], []

    for uname in usernames:
        try:
            user = get_user_by_username(uname)
            if not user:
                not_found.append(uname)
                continue

            add_points_to_user(user['user_id'], amount)
            updated.append(uname)

            # Log + coba DM user
            try:
                new_total = user['points'] + amount  # asumsinya kolom points di DB
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=(
                        f"🎉 Selamat *{uname}*!\n"
                        f"Kamu baru saja mendapatkan *+{amount}* poin dari Admin.\n\n"
                        f"🏆 Total poinmu sekarang: *{new_total}*"
                    ),
                    parse_mode="Markdown"
                )
            except Exception:
                pass

   

        except Exception as e:
            logger.error(f"Failed to add points for {uname}: {e}")
            failed.append(uname)

    # Susun hasil balasan
    lines = []
    if updated:
        lines.append("✅ Berhasil menambahkan *{}* poin ke:\n- {}".format(
            amount, "\n- ".join(updated)
        ))
    if not_found:
        lines.append("❌ Username tidak ditemukan:\n- {}".format("\n- ".join(not_found)))
    if failed:
        lines.append("⚠️ Gagal diproses:\n- {}".format("\n- ".join(failed)))

    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")

