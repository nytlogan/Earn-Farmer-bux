"""
handlers/wallet.py — 💰 Wallet button handler.
"""

import telebot

from config import MIN_WITHDRAWAL
from database import get_balance, clear_state, audit
from keyboards import back_keyboard


def register(bot: telebot.TeleBot) -> None:
    pass  # called directly from main_handler


def handle_wallet(bot: telebot.TeleBot, uid: int) -> None:
    clear_state(uid)
    bal = get_balance(uid)
    audit(uid, "wallet_view")
    bot.send_message(
        uid,
        f"💰 *Your Wallet*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💎 Balance: *{bal:.2f}\\$*\n\n"
        f"Minimum withdrawal: *{MIN_WITHDRAWAL:.2f}\\$*",
        parse_mode="MarkdownV2",
        reply_markup=back_keyboard(),
    )

