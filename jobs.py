from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from decorators import admin_only
from db import (
    add_job, get_all_jobs, get_job_by_id, add_applicant, get_applicants_by_job,
    get_user_by_id, add_badge_to_user, has_badge, get_total_applies, get_conn
)
from utils import sanitize_input, get_user_display_name, GROUP_ID, BUZZER_TOPIC_ID, INFLUENCER_TOPIC_ID, PAYMENT_TOPIC_ID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ======== ACTIVITY LOGGING ========
def log_activity(action_type, user_id=None, description=""):
    """Simple activity logging function"""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            # Create activity log table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action_type TEXT,
                    user_id TEXT,
                    description TEXT
                )
            """)
            # Insert activity log
            cur.execute("""
                INSERT INTO activity_logs (action_type, user_id, description)
                VALUES (?, ?, ?)
            """, (action_type, user_id, description))
            conn.commit()
    except Exception as e:
        logger.debug(f"Activity logging failed: {e}")
        # Don't raise exception - logging is not critical

# ======== POST JOB CONVERSATION STATES ========
POSTJOB_TITLE, POSTJOB_FEE, POSTJOB_DESC, POSTJOB_TOPIC = range(4)

@admin_only
async def postjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start job posting process"""
    await update.message.reply_text(
        "📝 *Posting Job Baru*\n\n"
        "Langkah 1/4: Masukkan judul job\n\n"
        "💡 *Tips:* Buat judul yang menarik dan jelas",
        parse_mode="Markdown"
    )
    return POSTJOB_TITLE

async def postjob_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job title input"""
    title = sanitize_input(update.message.text.strip())

    if len(title) < 5:
        await update.message.reply_text("❌ Judul terlalu pendek (minimal 5 karakter). Coba lagi:")
        return POSTJOB_TITLE

    context.user_data['postjob_title'] = title
    await update.message.reply_text(
        "💰 *Langkah 2/4: Fee/Gaji*\n\n"
        "Masukkan nominal fee (contoh: 10000 atau 10k atau 10rb)\n\n"
        "💡 Bisa juga format seperti: '5k-10k' untuk range",
        parse_mode="Markdown"
    )
    return POSTJOB_FEE

async def postjob_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job fee input"""
    fee = sanitize_input(update.message.text.strip())

    if len(fee) < 2:
        await update.message.reply_text("❌ Fee tidak boleh kosong. Masukkan nominal yang valid:")
        return POSTJOB_FEE

    context.user_data['postjob_fee'] = fee
    await update.message.reply_text(
        "📋 *Langkah 3/4: Deskripsi Job*\n\n"
        "Masukkan deskripsi lengkap job:\n"
        "• Apa yang harus dilakukan\n"
        "• Syarat/ketentuan\n"
        "• Deadline (jika ada)\n"
        "• Link yang perlu diakses\n\n"
        "💡 Gunakan format yang jelas dan mudah dipahami",
        parse_mode="Markdown"
    )
    return POSTJOB_DESC

async def postjob_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job description input"""
    desc = sanitize_input(update.message.text.strip(), max_length=2000)

    if len(desc) < 10:
        await update.message.reply_text("❌ Deskripsi terlalu pendek (minimal 10 karakter). Coba lagi:")
        return POSTJOB_DESC

    context.user_data['postjob_desc'] = desc

    # Show topic selection
    keyboard = [
        [
            InlineKeyboardButton("🎯 Buzzer", callback_data="topic_buzzer"),
            InlineKeyboardButton("🌟 Influencer", callback_data="topic_influencer")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📍 *Langkah 4/4: Pilih Kategori*\n\n"
        "🎯 **Buzzer** - Untuk job buzzer/promosi umum\n"
        "🌟 **Influencer** - Untuk job khusus influencer\n\n"
        "Pilih kategori yang sesuai:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return POSTJOB_TOPIC

async def postjob_topic_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle topic selection and create job"""
    query = update.callback_query
    await query.answer()

    try:
        # Get stored data
        title = context.user_data['postjob_title']
        fee = context.user_data['postjob_fee']
        desc = context.user_data['postjob_desc']

        # Determine topic based on selection
        if query.data == "topic_buzzer":
            topic_id = BUZZER_TOPIC_ID
            topic_name = "Buzzer"
            topic_emoji = "🎯"
        elif query.data == "topic_influencer":
            topic_id = INFLUENCER_TOPIC_ID
            topic_name = "Influencer"
            topic_emoji = "🌟"
        else:
            await query.edit_message_text("❌ Pilihan tidak valid.")
            return ConversationHandler.END

        # Create job in database
        job_id = add_job(title, fee, desc, status="aktif")

        # Create job post message
        job_text = (
            f"📢 *JOB BARU - {topic_emoji} {topic_name.upper()}*\n\n"
            f"🆔 **ID:** {job_id}\n"
            f"📌 **Judul:** {title}\n"
            f"💰 **Fee:** {fee}\n\n"
            f"📋 **Deskripsi:**\n{desc}\n\n"
            f"🟢 **Status:** Aktif"
        )

        # Create apply button
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Apply Job", callback_data=f"apply_{job_id}")]
        ])

        # Send to appropriate topic
        target_chat_id = GROUP_ID
        send_kwargs = {
            "chat_id": target_chat_id,
            "text": job_text,
            "parse_mode": "Markdown",
            "reply_markup": reply_markup,
            "message_thread_id": topic_id
        }

        await context.bot.send_message(**send_kwargs)

        # Confirm to admin
        await query.edit_message_text(
            f"✅ *Job Berhasil Diposting!*\n\n"
            f"🆔 **Job ID:** {job_id}\n"
            f"📍 **Kategori:** {topic_name} ({topic_emoji})\n"
            f"📌 **Judul:** {title}\n\n"
            f"Job telah diposting ke grup dan siap menerima aplikasi!",
            parse_mode="Markdown"
        )

        # Log activity
        log_activity("job_posted", str(query.from_user.id), f"Job {job_id} posted: {title}")

    except Exception as e:
        logger.error(f"Failed to post job: {e}")
        await query.edit_message_text(
            "❌ Terjadi kesalahan saat memposting job. Silakan coba lagi."
        )

    return ConversationHandler.END

async def postjob_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel job posting"""
    await update.message.reply_text("❌ Posting job dibatalkan.")
    return ConversationHandler.END

# Job posting conversation handler
postjob_conv = ConversationHandler(
    entry_points=[CommandHandler("postjob", postjob_command)],
    states={
        POSTJOB_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, postjob_title)],
        POSTJOB_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, postjob_fee)],
        POSTJOB_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, postjob_desc)],
        POSTJOB_TOPIC: [CallbackQueryHandler(postjob_topic_selection, pattern="^topic_(buzzer|influencer)$")],
    },
    fallbacks=[CommandHandler("cancel", postjob_cancel)],
)

# ======== UPDATE JOB ========

@admin_only
async def updatejob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update job status"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "📝 *Update Job Status*\n\n"
            "**Penggunaan:** `/updatejob <ID> <status>`\n\n"
            "**Status yang tersedia:**\n"
            "• `aktif` - Job masih buka\n"
            "• `close` - Job ditutup\n"
            "• `cair` - Job sudah dibayar\n\n"
            "**Contoh:** `/updatejob 1 close`",
            parse_mode="Markdown"
        )
        return

    try:
        job_id, status = context.args[0], context.args[1].lower()

        # Validate job exists
        job = get_job_by_id(job_id)
        if not job:
            await update.message.reply_text(f"❌ Job dengan ID {job_id} tidak ditemukan.")
            return

        # Validate status
        valid_statuses = ["aktif", "close", "cair"]
        if status not in valid_statuses:
            await update.message.reply_text(
                f"❌ Status tidak valid. Gunakan: {', '.join(valid_statuses)}"
            )
            return

        # Update status in database
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, job_id)
            )
            conn.commit()

        await update.message.reply_text(
            f"✅ *Job {job_id} Updated*\n\n"
            f"Status berhasil diubah ke: **{status.upper()}**",
            parse_mode="Markdown"
        )

        # Send notification to group if status is 'cair'
        if status == "cair":
            try:
                notif = (
                    f"💸 *PEMBAYARAN JOB {job_id}*\n\n"
                    f"🎉 Job **{job['title']}** sudah **CAIR**!\n\n"
                    f"Selamat buat semua pelamar yang berhasil! 🎊"
                )

                send_kwargs = {
                    "chat_id": GROUP_ID,
                    "text": notif,
                    "parse_mode": "Markdown"
                }

                if PAYMENT_TOPIC_ID:
                    send_kwargs["message_thread_id"] = PAYMENT_TOPIC_ID

                await context.bot.send_message(**send_kwargs)
            except Exception as e:
                logger.error(f"Failed to send payment notification: {e}")

        log_activity("job_updated", str(update.effective_user.id), f"Job {job_id} status changed to {status}")

    except Exception as e:
        logger.error(f"Failed to update job: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mengupdate job.")

@admin_only
async def resetjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset/delete jobs"""
    if not context.args:
        await update.message.reply_text(
            "🗑️ *Reset Job*\n\n"
            "**Penggunaan:**\n"
            "• `/resetjob all` - Hapus semua job\n"
            "• `/resetjob <ID>` - Hapus job tertentu\n\n"
            "⚠️ **Peringatan:** Tindakan ini tidak bisa dibatalkan!",
            parse_mode="Markdown"
        )
        return

    try:
        arg = context.args[0]

        with get_conn() as conn:
            cur = conn.cursor()

            if arg.lower() == "all":
                # Delete all jobs and applications
                cur.execute("DELETE FROM applicants")
                cur.execute("DELETE FROM jobs")
                conn.commit()

                await update.message.reply_text("✅ Semua job dan aplikasi telah dihapus.")
                log_activity("reset_jobs", str(update.effective_user.id), "All jobs deleted")

            else:
                # Delete specific job
                job_id = arg
                job = get_job_by_id(job_id)

                if not job:
                    await update.message.reply_text(f"❌ Job dengan ID {job_id} tidak ditemukan.")
                    return

                cur.execute("DELETE FROM applicants WHERE job_id = ?", (job_id,))
                cur.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                conn.commit()

                await update.message.reply_text(f"✅ Job {job_id} telah dihapus.")
                log_activity("delete_job", str(update.effective_user.id), f"Job {job_id} deleted")

    except Exception as e:
        logger.error(f"Failed to reset jobs: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat menghapus job.")

@admin_only
async def pelamarjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show job applicants"""
    if not context.args:
        await update.message.reply_text(
            "👥 *Lihat Pelamar Job*\n\n"
            "**Penggunaan:** `/pelamarjob <ID>`\n\n"
            "**Contoh:** `/pelamarjob 1`",
            parse_mode="Markdown"
        )
        return

    try:
        job_id = context.args[0]
        job = get_job_by_id(job_id)

        if not job:
            await update.message.reply_text(f"❌ Job dengan ID {job_id} tidak ditemukan.")
            return

        applicants = get_applicants_by_job(job_id)

        if not applicants:
            await update.message.reply_text(
                f"📭 *Job {job_id}: {job['title']}*\n\n"
                "Belum ada yang apply untuk job ini.",
                parse_mode="Markdown"
            )
            return

        text = f"👥 *Pelamar Job {job_id}*\n"
        text += f"📌 **{job['title']}**\n"
        text += f"💰 **Fee:** {job['fee']}\n"
        text += f"🟢 **Status:** {job['status']}\n\n"
        text += f"👥 **Total Pelamar:** {len(applicants)} orang\n\n"

        for i, user_id in enumerate(applicants, start=1):
            user = get_user_by_id(user_id)
            if user:
                username = user['username']
                text += f"{i}. {username}\n"
            else:
                text += f"{i}. User {user_id} (data tidak ditemukan)\n"

        await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Failed to get job applicants: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mengambil data pelamar.")

# ======== LIST JOB ========

async def listjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all available jobs"""
    try:
        jobs = get_all_jobs()

        if not jobs:
            await update.message.reply_text(
                "📭 *Belum Ada Job Tersedia*\n\n"
                "Saat ini belum ada job yang diposting. Pantau terus grup untuk job terbaru!",
                parse_mode="Markdown"
            )
            return

        # Separate jobs by status
        aktif_jobs = [job for job in jobs if job['status'] == 'aktif']
        other_jobs = [job for job in jobs if job['status'] != 'aktif']

        text = "📋 *Daftar Job Tersedia*\n\n"

        if aktif_jobs:
            text += "🟢 **Job Aktif:**\n"
            for job in aktif_jobs[:10]:  # Limit to 10 active jobs
                text += f"🆔 {job['id']} | {job['title']} | 💰 {job['fee']}\n"

        if other_jobs:
            text += f"\n📊 **Job Lainnya:**\n"
            for job in other_jobs[:5]:  # Limit to 5 other jobs
                status_emoji = "🔴" if job['status'] == 'close' else "💸"
                text += f"{status_emoji} {job['id']} | {job['title']} | {job['status']}\n"

        text += f"\n💡 **Total Job:** {len(jobs)}\n"
        text += f"📝 Gunakan `/infojob <id>` untuk detail job\n"
        text += f"📌 Contoh: `/infojob 1`"

        await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mengambil daftar job.")

# ======== INFO JOB ========

async def infojob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed job information"""
    if not context.args:
        await update.message.reply_text(
            "📋 *Info Detail Job*\n\n"
            "**Penggunaan:** `/infojob <ID>`\n\n"
            "**Contoh:** `/infojob 1`",
            parse_mode="Markdown"
        )
        return

    try:
        job_id = context.args[0]
        job = get_job_by_id(job_id)

        if not job:
            await update.message.reply_text(f"❌ Job dengan ID {job_id} tidak ditemukan.")
            return

        # Get applicant count
        applicants = get_applicants_by_job(job_id)
        applicant_count = len(applicants)

        # Status emoji
        status_emoji = {
            'aktif': '🟢',
            'close': '🔴',
            'cair': '💸'
        }.get(job['status'], '⚪')

        job_text = (
            f"📋 *Detail Job*\n\n"
            f"🆔 **ID:** {job['id']}\n"
            f"📌 **Judul:** {job['title']}\n"
            f"💰 **Fee:** {job['fee']}\n"
            f"{status_emoji} **Status:** {job['status'].upper()}\n"
            f"👥 **Pelamar:** {applicant_count} orang\n\n"
            f"📋 **Deskripsi:**\n{job['desc']}\n\n"
            f"📅 **Dibuat:** {job.get('created_at', 'Unknown')}"
        )

        # Only show apply button if job is active
        if job['status'] == 'aktif':
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Apply Job", callback_data=f"apply_{job_id}")]
            ])
            await update.message.reply_text(job_text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await update.message.reply_text(job_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Failed to get job info: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan saat mengambil info job.")

# ======== APPLY BUTTON HANDLER ========

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    print(f"🔧 DEBUG: jobs.py button_handler called with data: {query.data}") # Added debug log
    await query.answer()

    # Check if the callback is for applying to a job
    if query.data.startswith("apply_"):
        await apply_button(update, context)
    # Add other button handlers here if needed in the future
    # elif query.data.startswith("other_action_"):
    #     await other_action_handler(update, context)

async def apply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job application button press"""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    user_display = get_user_display_name(query.from_user)

    try:
        # Check if user is registered
        user_data = get_user_by_id(user_id)
        if not user_data:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "❌ *Registrasi Diperlukan*\n\n"
                        "Kamu harus mendaftar terlebih dahulu sebelum bisa apply job.\n\n"
                        "👉 Ketik `/register` untuk memulai pendaftaran."
                    ),
                    parse_mode="Markdown"
                )
            except:
                pass  # User might have blocked bot
            return

        # Extract job ID from callback data
        job_id = query.data.split("_")[1]
        job = get_job_by_id(job_id)

        if not job:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ Job tidak ditemukan atau sudah dihapus."
                )
            except:
                pass
            return

        # Check if job is still active
        if job['status'] != 'aktif':
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Job {job_id} sudah tidak aktif (status: {job['status']})"
                )
            except:
                pass
            return

        # Check if user already applied
        applicants = get_applicants_by_job(job_id)
        if user_id in applicants:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"⚠️ *Sudah Apply*\n\n"
                        f"Kamu sudah apply untuk job **{job['title']}** (ID: {job_id})\n\n"
                        f"Tunggu pengumuman dari admin ya!"
                    ),
                    parse_mode="Markdown"
                )
            except:
                pass
            return

        # Add user as applicant
        add_applicant(job_id, user_id)

        # Check and award achievement badges
        total_applies = get_total_applies(user_id)

        # Badge: Rising Star (first apply)
        if total_applies == 1 and not has_badge(user_id, "🚀 Rising Star"):
            add_badge_to_user(user_id, "🚀 Rising Star")
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🚀 *Congratulations!* Kamu mendapat badge **Rising Star** untuk apply job pertama kali!",
                    parse_mode="Markdown"
                )
            except:
                pass

        # Badge: Member Aktif (10 applies)
        if total_applies >= 10 and not has_badge(user_id, "🎯 Member Aktif"):
            add_badge_to_user(user_id, "🎯 Member Aktif")
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎯 *Amazing!* Kamu mendapat badge **Member Aktif** karena sudah apply 10+ job!",
                    parse_mode="Markdown"
                )
            except:
                pass

        # Badge: Worker Pro (50 applies)
        if total_applies >= 50 and not has_badge(user_id, "💼 Worker Pro"):
            add_badge_to_user(user_id, "💼 Worker Pro")
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="💼 *Incredible!* Kamu sekarang **Worker Pro** dengan 50+ job apply!",
                    parse_mode="Markdown"
                )
            except:
                pass

        # Get updated applicant list and position
        updated_applicants = get_applicants_by_job(job_id)
        user_position = updated_applicants.index(user_id) + 1
        total_applicants = len(updated_applicants)

        # Send success notification
        try:
            success_msg = (
                f"✅ *Apply Berhasil!*\n\n"
                f"📌 **Job:** {job['title']}\n"
                f"🆔 **ID:** {job_id}\n"
                f"💰 **Fee:** {job['fee']}\n\n"
                f"🎯 **Posisi Kamu:** #{user_position} dari {total_applicants} pelamar\n"
                f"💰 **Bonus:** 2-5 poin akan di tambahkan setelah selesai mengerjakan job\n\n"
                f"📋 **Daftar Pelamar Saat Ini:**\n"
            )

            # Show top 10 applicants
            for i, applicant_id in enumerate(updated_applicants[:10], 1):
                applicant = get_user_by_id(applicant_id)
                if applicant:
                    username = applicant['username']
                    if applicant_id == user_id:
                        success_msg += f"👉 {i}. **{username}** (kamu)\n"
                    else:
                        success_msg += f"{i}. {username}\n"

            if len(updated_applicants) > 10:
                success_msg += f"... dan {len(updated_applicants) - 10} lainnya\n"

            success_msg += f"\n🎉 Good luck! Tunggu pengumuman dari admin ya!"

            await context.bot.send_message(
                chat_id=user_id,
                text=success_msg,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Failed to send success notification: {e}")

        # Log activity
        log_activity("job_apply", user_id, f"Applied to job {job_id}: {job['title']}")

    except Exception as e:
        logger.error(f"Failed to process job application: {e}")
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Terjadi kesalahan saat memproses aplikasi. Silakan coba lagi."
            )
        except:
            pass