from telegram import Update
from telegram.ext import ContextTypes
from db import (
    get_all_users, get_user_by_id, get_referrals_by_username, 
    add_badge_to_user, has_badge, get_badges
)
from utils import format_currency
import logging

logger = logging.getLogger(__name__)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard with top members"""
    try:
        users = get_all_users()
        
        if not users:
            await update.message.reply_text(
                "📭 *Leaderboard Kosong*\n\n"
                "Belum ada member yang terdaftar untuk ditampilkan di leaderboard.",
                parse_mode="Markdown"
            )
            return

        # Calculate additional stats for each user
        enhanced_users = []
        for user in users:
            referrals = get_referrals_by_username(user['username'])
            referral_count = len(referrals)
            user['referral_count'] = referral_count
            enhanced_users.append(user)

        # Sort by points (descending)
        top_points = sorted(enhanced_users, key=lambda x: x.get('points', 0), reverse=True)[:10]
        
        # Sort by referrals (descending)
        top_referrals = sorted(enhanced_users, key=lambda x: x['referral_count'], reverse=True)[:10]

        # Award Top Contributor badge to #1 in points
        if top_points and top_points[0].get('points', 0) > 0:
            top_user = top_points[0]
            if not has_badge(top_user['user_id'], "🏆 Top Contributor"):
                add_badge_to_user(top_user['user_id'], "🏆 Top Contributor")
                try:
                    await context.bot.send_message(
                        chat_id=top_user['user_id'],
                        text="🏆 *Congratulations!* Kamu sekarang **Top Contributor** bulan ini!",
                        parse_mode="Markdown"
                    )
                except:
                    pass  # User might have blocked bot

        # Build leaderboard message
        text = "🏆 *NEXOBUZZ LEADERBOARD*\n\n"
        
        # Top Points Section
        text += "💰 *TOP POINTS*\n"
        if top_points:
            for i, user in enumerate(top_points, start=1):
                points = user.get('points', 0)
                badges = get_badges(user['user_id'])
                badge_display = badges[0] if badges else ""
                
                # Medal emojis for top 3
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = f"{i}."
                
                text += f"{medal} `{user['username']}` - {points} poin {badge_display}\n"
        else:
            text += "Belum ada data\n"

        text += "\n👥 *TOP REFERRERS*\n"
        if top_referrals and any(user['referral_count'] > 0 for user in top_referrals):
            for i, user in enumerate(top_referrals[:5], start=1):
                if user['referral_count'] > 0:
                    text += f"{i}. `{user['username']}` - {user['referral_count']} referral\n"
        else:
            text += "Belum ada referral\n"

        # Statistics
        total_users = len(users)
        total_points = sum(user.get('points', 0) for user in users)
        total_referrals = sum(user['referral_count'] for user in enhanced_users)
        
        text += f"\n📊 *STATISTIK KOMUNITAS*\n"
        text += f"👥 Total Member: {total_users}\n"
        text += f"💰 Total Points: {total_points:,}\n"
        text += f"🔗 Total Referrals: {total_referrals}\n"
        text += f"💵 Nilai Points: {format_currency(total_points * 10)}\n\n"
        
        text += "💡 Gunakan `/points` untuk cek poin kamu!"

        await update.message.reply_text(text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Failed to generate leaderboard: {e}")
        await update.message.reply_text(
            "❌ Terjadi kesalahan saat membuat leaderboard. Silakan coba lagi."
        )

async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's current points and earning information"""
    try:
        user_id = str(update.effective_user.id)
        user_data = get_user_by_id(user_id)
        
        if not user_data:
            await update.message.reply_text(
                "❌ *Kamu Belum Terdaftar*\n\n"
                "Gunakan `/register` untuk mendaftar sebagai member dan mulai mengumpulkan poin!",
                parse_mode="Markdown"
            )
            return

        # Get user stats
        points = user_data.get('points', 0)
        username = user_data['username']
        referrals = get_referrals_by_username(username)
        referral_count = len(referrals)
        badges = get_badges(user_id)
        
        # Calculate referral points
        referral_points = referral_count * 25
        
        # Get user ranking
        all_users = get_all_users()
        sorted_users = sorted(all_users, key=lambda x: x.get('points', 0), reverse=True)
        user_rank = next((i + 1 for i, user in enumerate(sorted_users) if user['user_id'] == user_id), "N/A")
        
        msg = f"💰 *POINT DASHBOARD*\n\n"
        msg += f"👤 **{username}**\n"
        msg += f"💰 **Point Sekarang:** {points:,}\n"
        msg += f"📊 **Ranking:** #{user_rank} dari {len(all_users)}\n"
        msg += f"💵 **Nilai Tukar:** {format_currency(points * 10)}\n\n"
        
        msg += f"🏅 **Badge:** {' | '.join(badges) if badges else 'Belum ada'}\n\n"
        
        msg += f"📈 *EARNING BREAKDOWN*\n"
        msg += f"🔗 Referral Bonus: {referral_points:,} poin ({referral_count} referral)\n"
        msg += f"⚡ Activity Points: {points - referral_points:,} poin\n\n"
        
        msg += f"💡 *CARA MENDAPAT POIN*\n"
        msg += f"• Apply job: +2-5 poin\n"
        msg += f"• Aktif di grup: +1 poin\n"
        msg += f"• Follow Sosmed +1 poin\n"
        msg += f"• Referral berhasil: +25 poin\n"
        
        msg += f"🎯 *NEXT GOALS*\n"
        if points < 100:
            msg += f"• Kumpulkan {100 - points} poin lagi untuk mencapai 100 poin\n"
        if referral_count < 5:
            msg += f"• Ajak {5 - referral_count} teman lagi untuk 5 referral\n"
        if not has_badge(user_id, "🎯 Member Aktif"):
            from db import get_total_applies
            applies = get_total_applies(user_id)
            if applies < 10:
                msg += f"• Apply {10 - applies} job lagi untuk badge Member Aktif\n"
        
        msg += f"\n🔗 **Kode Referral:** `{username}`\n"
        msg += f"👥 Gunakan `/myreferral` untuk detail referral\n"
        msg += f"🏆 Gunakan `/leaderboard` untuk ranking komunitas"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Failed to show points: {e}")
        await update.message.reply_text(
            "❌ Terjadi kesalahan saat mengambil data poin. Silakan coba lagi."
        )
