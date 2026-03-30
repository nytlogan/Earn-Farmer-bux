"""
handlers/withdrawal.py — Withdrawal flow for Binance and bkash.
"""

import telebot

from config import OWNER_ID, MIN_WITHDRAWAL
from database import (
    get_balance,
    set_balance,
    get_conn,
    record_withdrawal_request,
    clear_state,
    audit,
)
from keyboards import main_menu_keyboard, withdraw_method_keyboard, remove_keyboard
from utils.validators import is_valid_binance_address, is_valid_bkash_number, sanitise_text
from utils.logger import logger


def register(bot: telebot.TeleBot) -> None:
    pass  # called directly from main_handler


def handle_withdraw_menu(bot: telebot.TeleBot, uid: int) -> None:
    clear_state(uid)
    bot.send_message(
        uid,
        "💸 *Withdraw*\n"
        "━━━━━━━━━━━━━━━\n"
        "Choose your withdrawal method 👇",
        parse_mode="MarkdownV2",
        reply_markup=withdraw_method_keyboard(),
    )


def handle_binance_prompt(bot: telebot.TeleBot, uid: int) -> None:
    from database import set_state
    set_state(uid, "awaiting_binance_address")
    bot.send_message(
        uid,
        "🔐 *Binance Withdrawal*\n"
        "━━━━━━━━━━━━━━━\n"
        "Enter your *\\(BEP\\-20\\)* wallet address 👇",
        parse_mode="MarkdownV2",
        reply_markup=remove_keyboard(),
    )


def handle_bkash_prompt(bot: telebot.TeleBot, uid: int) -> None:
    from database import set_state
    set_state(uid, "awaiting_bkash_number")
    bot.send_message(
        uid,
        "📱 *bkash Withdrawal*\n"
        "━━━━━━━━━━━━━━━\n"
        "Enter your *bkash Number* 👇",
        parse_mode="MarkdownV2",
        reply_markup=remove_keyboard(),
    )


def process_withdrawal(
    bot: telebot.TeleBot, uid: int, message, method: str
) -> None:
    """Validate input, deduct balance, log the request, and notify owner."""
    bal = get_balance(uid)
    clear_state(uid)

    # ── Minimum balance check ─────────────────────────────────────────────────
    if bal < MIN_WITHDRAWAL:
        try:
            bot.send_message(
                uid,
                f"❌ *Minimum withdrawal is {MIN_WITHDRAWAL:.2f}\\$*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💰 Your Balance: *{bal:.2f}\\$*\n"
                f"📉 You need: *{(MIN_WITHDRAWAL - bal):.2f}\\$* more",
                parse_mode="MarkdownV2",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as exc:
            logger.error("withdraw balance-check msg error uid=%s: %s", uid, exc)
        return

    address = sanitise_text(message.text, max_len=100)

    # ── Address / number format validation ────────────────────────────────────
    if method == "Binance" and not is_valid_binance_address(address):
        bot.send_message(
            uid,
            "❌ Invalid BEP\\-20 address\\.\n"
            "Please enter a valid wallet address starting with `0x`\\.",
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )
        audit(uid, "withdrawal_invalid_address", f"method={method}")
        return

    if method == "bkash" and not is_valid_bkash_number(address):
        bot.send_message(
            uid,
            "❌ Invalid bkash number\\.\n"
            "Please enter a valid Bangladeshi mobile number \\(e\\.g\\. 01XXXXXXXXX\\)\\.",
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )
        audit(uid, "withdrawal_invalid_address", f"method={method}")
        return

    # ── Atomically zero the balance and record request ────────────────────────
    set_balance(uid, 0.0)
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET withdrawals_count = withdrawals_count + 1 WHERE uid = ?",
            (uid,),
        )
    record_withdrawal_request(uid, method, address, bal)
    audit(uid, "withdrawal_submitted", f"method={method} amount={bal:.2f}")

    try:
        bot.send_message(
            uid,
            f"✅ *Withdrawal Submitted\\!*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💸 Amount: *{bal:.2f}\\$*\n"
            f"🏦 Method: *{_escape(method)}*\n"
            f"📬 Address: `{_escape(address)}`\n\n"
            f"⏳ Processing time: 24\\-48 hours",
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as exc:
        logger.error("withdrawal notify user error uid=%s: %s", uid, exc)

    try:
        full_name = message.from_user.full_name or "N/A"
        bot.send_message(
            OWNER_ID,
            f"💸 *Withdrawal Request\\!*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 Name: {_escape(full_name)}\n"
            f"🆔 User ID: `{uid}`\n"
            f"🏦 Method: *{_escape(method)}*\n"
            f"📬 Address: `{_escape(address)}`\n"
            f"💰 Amount: *{bal:.2f}\\$*",
            parse_mode="MarkdownV2",
        )
    except Exception:
        pass

    logger.info("Withdrawal submitted uid=%s method=%s amount=%.2f", uid, method, bal)


def _escape(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in str(text))
                  
