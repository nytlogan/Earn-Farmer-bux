"""
handlers/profile.py — /profile command and 👤 Profile button.
"""

import telebot

from database import (
    ensure_profile,
    get_profile,
    get_balance,
    can_claim_bonus,
    time_until_next_bonus,
    clear_state,
    audit,
)
from keyboards import back_keyboard
from utils.logger import logger


def register(bot: telebot.TeleBot) -> None:

    @bot.message_handler(commands=["profile"])
    def cmd_profile(message):
        uid = message.from_user.id
        ensure_profile(uid, message.from_user.full_name or "User")
        clear_state(uid)
        show_profile(bot, uid)
        audit(uid, "profile_view")


def show_profile(bot: telebot.TeleBot, uid: int) -> None:
    profile      = get_profile(uid)
    bal          = get_balance(uid)
    bonus_status = (
        "✅ Available" if can_claim_bonus(uid)
        else f"⏳ {time_until_next_bonus(uid)}"
    )

    text = (
        f"👤 *Your Profile*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 User ID: `{uid}`\n"
        f"📛 Name: {_escape(profile.get('name', 'N/A'))}\n"
        f"📅 Joined: {_escape(profile.get('join_date', 'N/A'))}\n\n"
        f"💰 Balance: *{bal:.2f}\\$*\n"
        f"✅ Tasks Done: *{profile.get('tasks_count', 0)}*\n"
        f"💸 Total Withdrawn: *{profile.get('withdrawals_count', 0)}*\n"
        f"👥 Referrals: *{profile.get('referrals_count', 0)}*\n\n"
        f"🎁 Daily Bonus: {bonus_status}"
    )
    try:
        bot.send_message(
            uid, text, parse_mode="MarkdownV2",
            reply_markup=back_keyboard(),
        )
    except Exception as exc:
        logger.error("show_profile error uid=%s: %s", uid, exc)


def _escape(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in str(text))
  
