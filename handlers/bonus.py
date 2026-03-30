"""
handlers/bonus.py — 🎁 Daily Bonus button handler.
"""

import telebot

from config import DAILY_BONUS_AMOUNT
from database import (
    can_claim_bonus,
    add_balance,
    record_bonus_claim,
    get_balance,
    time_until_next_bonus,
    clear_state,
    audit,
)
from keyboards import main_menu_keyboard


def register(bot: telebot.TeleBot) -> None:
    pass  # called directly from main_handler


def handle_daily_bonus(bot: telebot.TeleBot, uid: int) -> None:
    clear_state(uid)

    if can_claim_bonus(uid):
        add_balance(uid, DAILY_BONUS_AMOUNT)
        record_bonus_claim(uid)
        audit(uid, "bonus_claimed", f"amount={DAILY_BONUS_AMOUNT:.2f}")
        bot.send_message(
            uid,
            f"🎁 *Daily Bonus Claimed\\!*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 You received: *\\+{DAILY_BONUS_AMOUNT:.2f}\\$*\n"
            f"💎 New Balance: *{get_balance(uid):.2f}\\$*\n\n"
            f"⏳ Come back tomorrow for more\\!",
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )
    else:
        bot.send_message(
            uid,
            f"⏳ *Daily Bonus Not Ready*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"You already claimed today's bonus\\.\n\n"
            f"🕐 Next bonus in: *{time_until_next_bonus(uid)}*",
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
      )
      
