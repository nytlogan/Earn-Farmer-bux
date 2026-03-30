"""
handlers/referral.py — 🫂 Referral button handler.
"""

import telebot

from config import REFERRAL_BONUS
from database import get_profile, clear_state, audit
from keyboards import back_keyboard
from utils.logger import logger


def register(bot: telebot.TeleBot) -> None:
    pass  # called directly from main_handler


def handle_referral(bot: telebot.TeleBot, uid: int) -> None:
    clear_state(uid)
    audit(uid, "referral_view")

    try:
        bot_info = bot.get_me()
        ref_link = f"[t](https://t\\.me/{bot_info.username}?start\\={uid})"
    except Exception as exc:
        logger.error("get_me error: %s", exc)
        ref_link = "Unable to generate link"

    profile   = get_profile(uid)
    ref_count = profile.get("referrals_count", 0)

    bot.send_message(
        uid,
        f"👥 *Referral System*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Invite friends & earn *{REFERRAL_BONUS:.2f}\\$* per referral\\!\n\n"
        f"🔗 *Your Referral Link:*\n"
        f"`{ref_link}`\n\n"
        f"👤 Total Referrals: *{ref_count}*\n"
        f"💰 Total Earned: *{ref_count * REFERRAL_BONUS:.2f}\\$*\n\n"
        f"📤 Share your link and start earning\\!",
        parse_mode="MarkdownV2",
        reply_markup=back_keyboard(),
    )
  
