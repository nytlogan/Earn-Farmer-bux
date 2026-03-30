"""
handlers/start.py — /start command handler including referral attribution.
"""

import telebot

from config import OWNER_ID, REFERRAL_BONUS
from database import (
    ensure_profile,
    get_profile,
    add_balance,
    get_balance,
    set_referrer,
    clear_state,
    clear_current_task,
    audit,
)
from keyboards import main_menu_keyboard
from utils.logger import logger


def register(bot: telebot.TeleBot) -> None:

    @bot.message_handler(commands=["start"])
    def cmd_start(message):
        uid       = message.from_user.id
        full_name = message.from_user.full_name or "User"
        username  = message.from_user.username or "N/A"

        clear_state(uid)
        clear_current_task(uid)
        ensure_profile(uid, full_name, username)
        audit(uid, "start")

        # ── Referral handling ────────────────────────────────────────────────
        parts = message.text.split()
        if len(parts) > 1:
            try:
                referrer_uid = int(parts[1])
                profile      = get_profile(uid)

                referrer_exists = bool(get_profile(referrer_uid))

                if (
                    referrer_uid != uid
                    and profile.get("referrer_id") is None
                    and referrer_exists
                ):
                    add_balance(referrer_uid, REFERRAL_BONUS)
                    set_referrer(uid, referrer_uid)
                    audit(
                        uid,
                        "referral_joined",
                        f"referred_by={referrer_uid}",
                    )

                    try:
                        bot.send_message(
                            referrer_uid,
                            f"🎉 *New Referral!*\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"👤 {full_name} joined using your link\\!\n"
                            f"💰 You earned *\\+{REFERRAL_BONUS:.2f}\\$*\n"
                            f"💎 New Balance: *{get_balance(referrer_uid):.2f}\\$*",
                            parse_mode="MarkdownV2",
                        )
                    except Exception:
                        pass

            except (ValueError, KeyError) as exc:
                logger.debug("Referral parse error for uid=%s: %s", uid, exc)

        # ── Notify owner ─────────────────────────────────────────────────────
        try:
            bot.send_message(
                OWNER_ID,
                f"👤 *New User Started Bot\\!*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"• Name: {_escape(full_name)}\n"
                f"• Username: @{_escape(username)}\n"
                f"• User ID: `{uid}`",
                parse_mode="MarkdownV2",
            )
        except Exception:
            pass

        _send_main_menu(bot, uid)
        logger.info("User %s started bot (name=%s)", uid, full_name)


def _send_main_menu(bot: telebot.TeleBot, uid: int, custom_text: str = None) -> None:
    text = custom_text or (
        "💎 *Earn Farmer*\n"
        "━━━━━━━━━━━━━━━\n"
        "Welcome\\! 👋\n\n"
        "Select an option below 👇"
    )
    try:
        bot.send_message(
            uid, text, parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as exc:
        logger.error("send_main_menu error uid=%s: %s", uid, exc)


def _escape(text: str) -> str:
    """Escape special characters for MarkdownV2."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in str(text))
  
