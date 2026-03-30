"""
handlers/main_handler.py — Central text message router.
All keyboard-button text is dispatched from here.
"""

import telebot

from database import (
    ensure_profile,
    get_state,
    clear_state,
    clear_current_task,
    is_banned,
    audit,
)
from keyboards import main_menu_keyboard
from utils.rate_limiter import check_rate_limit
from utils.logger import logger

# ── Import feature handlers ───────────────────────────────────────────────────
from handlers.profile   import show_profile
from handlers.wallet    import handle_wallet
from handlers.withdrawal import (
    handle_withdraw_menu,
    handle_binance_prompt,
    handle_bkash_prompt,
    process_withdrawal,
)
from handlers.bonus     import handle_daily_bonus
from handlers.referral  import handle_referral


def send_main_menu(bot: telebot.TeleBot, uid: int, custom_text: str = None) -> None:
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


def register(bot: telebot.TeleBot) -> None:

    @bot.message_handler(func=lambda m: True, content_types=["text"])
    def handle_text(message):
        uid      = message.from_user.id
        text     = message.text.strip()
        state    = get_state(uid)

        ensure_profile(
            uid,
            message.from_user.full_name or "User",
            message.from_user.username or "N/A",
        )

        # ── Ban check ─────────────────────────────────────────────────────────
        if is_banned(uid):
            try:
                bot.send_message(
                    uid,
                    "🚫 You have been banned from using this bot\\.",
                    parse_mode="MarkdownV2",
                )
            except Exception:
                pass
            return

        # ── Rate limit check ──────────────────────────────────────────────────
        if not check_rate_limit(uid):
            try:
                bot.send_message(
                    uid,
                    "⚠️ You are sending messages too quickly\\. Please slow down\\.",
                    parse_mode="MarkdownV2",
                )
            except Exception:
                pass
            return

        try:
            # ── Withdrawal input states ───────────────────────────────────────
            if state == "awaiting_binance_address":
                process_withdrawal(bot, uid, message, method="Binance")
                return

            if state == "awaiting_bkash_number":
                process_withdrawal(bot, uid, message, method="bkash")
                return

            # ── Main menu buttons ─────────────────────────────────────────────
            if text == "📋 Tasks":
                bot._tasks_handle_tasks_menu(bot, uid)

            elif text == "💰 Wallet":
                handle_wallet(bot, uid)

            elif text == "💸 Withdraw":
                handle_withdraw_menu(bot, uid)

            elif text == "🫂 Referral":
                handle_referral(bot, uid)

            elif text == "🎁 Daily Bonus":
                handle_daily_bonus(bot, uid)

            elif text == "👤 Profile":
                clear_state(uid)
                show_profile(bot, uid)

            # ── Task flow buttons ─────────────────────────────────────────────
            elif text == "📧 Create Account - Earn 0.25$":
                bot._tasks_handle_start_task(bot, uid)

            elif text == "✅ Done":
                bot._tasks_handle_done(bot, uid)

            elif text == "❌ Cancel Task":
                bot._tasks_handle_cancel_task(bot, uid)

            # ── Withdrawal method buttons ─────────────────────────────────────
            elif text == "Binance ✅":
                handle_binance_prompt(bot, uid)

            elif text == "bkash ✅":
                handle_bkash_prompt(bot, uid)

            # ── Back ──────────────────────────────────────────────────────────
            elif text in ("🔙 Back", "Back 🔙"):
                clear_state(uid)
                clear_current_task(uid)
                send_main_menu(bot, uid)

            else:
                bot.send_message(
                    uid,
                    "⚠️ Please use the menu buttons below\\.",
                    parse_mode="MarkdownV2",
                    reply_markup=main_menu_keyboard(),
                )

        except Exception as exc:
            logger.error("handle_text error uid=%s text=%r: %s", uid, text, exc)
            audit(uid, "unhandled_error", str(exc))
            try:
                bot.send_message(
                    uid,
                    "⚠️ Something went wrong\\. Please try again\\.",
                    parse_mode="MarkdownV2",
                    reply_markup=main_menu_keyboard(),
                )
            except Exception:
                pass
          
