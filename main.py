import logging
from db import init_db
from health import start_health_server

from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ConversationHandler, ContextTypes
)
from telegram import Update
from dotenv import load_dotenv

from utils import ensure_env, BOT_TOKEN
from start import start, button_handler, check_milestone, new_member_handler, left_member_handler, hidden_tag_handler
from register import (
    register_command, username_step, referral_step, whatsapp_step, telegram_step,
    payment_method_step, payment_number_step, owner_name_step,
    editinfo_command, choose_field_step, edit_username_step, edit_whatsapp_step, edit_telegram_step,
    edit_payment_method_step, edit_payment_number_step, edit_owner_name_step,
    myinfo_command, myreferral_command,
    USERNAME, REFERRAL, WHATSAPP, TELEGRAM, PAYMENT_METHOD, PAYMENT_NUMBER, OWNER_NAME,
    CHOOSE_FIELD, EDIT_USERNAME, EDIT_WHATSAPP, EDIT_TELEGRAM, EDIT_PAYMENT_METHOD, EDIT_PAYMENT_NUMBER, EDIT_OWNER_NAME
)
from boost import (
    boost_command, boost_special_command, cek_booster_command,
    boost_button_handler, boost_description_handler, boost_special_description_handler,
    cancel_boost, BOOST_DESCRIPTION, BOOST_SPECIAL_DESCRIPTION
)
from ai import chat_with_ai, stop_ai_chat, start_ai_chat, save_group_messages, summary_command, group_activity_points
from admin import listmember_command, paymentinfo_command, memberinfo_command, delete_member_command, resetpoint_command, addbadge_command, resetapply_command, resetbadge_command, addpoint_command
from jobs import postjob_conv, postjob_command, updatejob_command, resetjob_command, pelamarjob_command, listjob_command, infojob_command, apply_button
from help import help_command
from leaderboard import leaderboard_command, points_command

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to initialize and run the bot"""
    try:
        # Initialize database
        init_db()
        print("✅ Database initialized successfully")

        # Ensure environment variables are set
        ensure_env()
        print("✅ Environment variables validated")

        # Create application with JobQueue
        from telegram.ext import JobQueue
        application = Application.builder().token(BOT_TOKEN).job_queue(JobQueue()).build()

        # Conversation handler untuk register
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("register", register_command, filters=filters.ChatType.PRIVATE)],
            states={
                USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username_step)],
                REFERRAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, referral_step)],
                WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, whatsapp_step)],
                TELEGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_step)],
                PAYMENT_METHOD: [CallbackQueryHandler(payment_method_step)],
                PAYMENT_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_number_step)],
                OWNER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_name_step)],
            },
            fallbacks=[],
        )

        # Conversation handler untuk editinfo
        editinfo_conv = ConversationHandler(
            entry_points=[CommandHandler("editinfo", editinfo_command)],
            states={
                CHOOSE_FIELD: [CallbackQueryHandler(choose_field_step)],
                EDIT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_username_step)],
                EDIT_WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_whatsapp_step)],
                EDIT_TELEGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_telegram_step)],
                EDIT_PAYMENT_METHOD: [CallbackQueryHandler(edit_payment_method_step)],
                EDIT_PAYMENT_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_payment_number_step)],
                EDIT_OWNER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_owner_name_step)],
            },
            fallbacks=[],
        )

        # Register conversation handlers
        application.add_handler(conv_handler)
        application.add_handler(editinfo_conv)

        # Register restriction for groups
        application.add_handler(
            CommandHandler("register",
                lambda u, c: u.message.reply_text("❌ Pendaftaran hanya via private chat. DM bot ya!"),
                filters=filters.ChatType.GROUPS
            )
        )

        # User commands
        application.add_handler(CommandHandler("myinfo", myinfo_command))
        application.add_handler(CommandHandler("myreferral", myreferral_command))

        # Jobs Feature
        application.add_handler(postjob_conv)

        # Admin job commands
        application.add_handler(CommandHandler("postjob", postjob_command))
        application.add_handler(CommandHandler("updatejob", updatejob_command))
        application.add_handler(CommandHandler("resetjob", resetjob_command))
        application.add_handler(CommandHandler("pelamarjob", pelamarjob_command))

        # Member job commands
        application.add_handler(CommandHandler("listjob", listjob_command))
        application.add_handler(CommandHandler("infojob", infojob_command))

        # Apply button
        application.add_handler(CallbackQueryHandler(apply_button, pattern=r"^apply_\d+$"))
        # Khusus tombol boost
        application.add_handler(CallbackQueryHandler(boost_button_handler, pattern=r"^boost:"))
        # Tombol start
        application.add_handler(CallbackQueryHandler(button_handler))

        #Start commands
        application.add_handler(
            CommandHandler("start", start, filters=filters.ChatType.PRIVATE)
        )
        application.add_handler(
            CommandHandler("start", lambda u, c: u.message.reply_text("❌ Command /start hanya bisa digunakan di private chat (DM bot)."), filters=filters.ChatType.GROUPS
            )
        )

        # Boost conversation handlers
        boost_conv = ConversationHandler(
            entry_points=[CommandHandler("boost", boost_command, filters=filters.ChatType.PRIVATE)],
            states={
                BOOST_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, boost_description_handler)],
            },
            fallbacks=[CommandHandler("cancel", cancel_boost)],
        )

        boost_special_conv = ConversationHandler(
            entry_points=[CommandHandler("boost_special", boost_special_command, filters=filters.ChatType.PRIVATE)],
            states={
                BOOST_SPECIAL_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, boost_special_description_handler)],
            },
            fallbacks=[CommandHandler("cancel", cancel_boost)],
        )

        application.add_handler(boost_conv)
        application.add_handler(boost_special_conv)
        application.add_handler(CommandHandler("cek_booster", cek_booster_command))

        # Restrict boost commands to private chat only
        application.add_handler(
            CommandHandler("boost",
                lambda u, c: u.message.reply_text("❌ Boost commands hanya bisa digunakan via private chat. DM bot ya!"),
                filters=filters.ChatType.GROUPS
            )
        )
        application.add_handler(
            CommandHandler("boost_special",
                lambda u, c: u.message.reply_text("❌ Boost commands hanya bisa digunakan via private chat. DM bot ya!"),
                filters=filters.ChatType.GROUPS
            )
        )

        # Special Messages
        # Member join
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
        # Member keluar
        application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, left_member_handler))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\..+'), hidden_tag_handler))

        # AI Features
        application.add_handler(CommandHandler("startai", start_ai_chat))
        application.add_handler(CommandHandler("stopai", stop_ai_chat))
        application.add_handler(CommandHandler("ai", chat_with_ai))

        # AI di private chat: interaktif TANPA /ai
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, chat_with_ai)
        )

        # Summary dan group activity
        application.add_handler(CommandHandler("summary", summary_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_group_messages))
        application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND, group_activity_points))

        # Admin Features
        application.add_handler(CommandHandler("listmember", listmember_command))
        application.add_handler(CommandHandler("paymentinfo", paymentinfo_command))
        application.add_handler(CommandHandler("memberinfo", memberinfo_command))
        application.add_handler(CommandHandler("delete", delete_member_command))
        application.add_handler(CommandHandler("resetpoint", resetpoint_command))
        application.add_handler(CommandHandler("addbadge", addbadge_command))
        application.add_handler(CommandHandler("resetapply", resetapply_command))
        application.add_handler(CommandHandler("resetbadge", resetbadge_command))

        # General commands
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("leaderboard", leaderboard_command))
        application.add_handler(CommandHandler("points", points_command))
        application.add_handler(CommandHandler("addpoint", addpoint_command))


        # Start services
        start_health_server()

        # Run the bot
        application.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Error starting bot: {e}")
        print("⚠️  Bot failed to start, but dashboard is still running on http://0.0.0.0:5000")
        print("📝 Please check your BOT_TOKEN and try again")

        # Keep the dashboard running even if bot fails
        try:
            import time
            print("🌐 Dashboard will continue running...")
            while True:
                time.sleep(60)  # Keep the process alive
        except KeyboardInterrupt:
            print("👋 Shutting down...")
            pass

if __name__ == "__main__":
    main()
