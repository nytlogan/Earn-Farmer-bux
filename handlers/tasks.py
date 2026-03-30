"""
handlers/tasks.py — Task menu, account-creation task flow, Done, Cancel.
"""

import telebot

from config import OWNER_ID, TASK_REWARD
from database import (
    get_current_task,
    set_current_task,
    clear_current_task,
    add_pending_task,
    get_profile,
    count_pending_tasks_for_user,
    clear_state,
    audit,
)
from keyboards import tasks_keyboard, task_action_keyboard, main_menu_keyboard
from utils.account_gen import generate_account
from utils.logger import logger

# Maximum pending tasks a user may have at once (anti-spam)
MAX_PENDING_PER_USER = 3


def register(bot: telebot.TeleBot) -> None:

    # ── Tasks menu button ────────────────────────────────────────────────────
    def handle_tasks_menu(bot: telebot.TeleBot, uid: int) -> None:
        clear_state(uid)
        clear_current_task(uid)
        bot.send_message(
            uid,
            "📋 *Tasks Menu*\n"
            "━━━━━━━━━━━━━━━\n"
            "Complete tasks to earn money\\! 💰",
            parse_mode="MarkdownV2",
            reply_markup=tasks_keyboard(),
        )

    # ── Start a new account task ─────────────────────────────────────────────
    def handle_start_task(bot: telebot.TeleBot, uid: int) -> None:
        clear_state(uid)

        # Anti-spam: cap pending tasks per user
        pending_count = count_pending_tasks_for_user(uid)
        if pending_count >= MAX_PENDING_PER_USER:
            bot.send_message(
                uid,
                f"⚠️ You already have *{pending_count}* pending tasks\\.\n"
                "Please wait for them to be reviewed before submitting more\\.",
                parse_mode="MarkdownV2",
                reply_markup=tasks_keyboard(),
            )
            return

        account = generate_account(uid)
        set_current_task(uid, account)
        audit(uid, "task_started", account.get("username", ""))

        bot.send_message(
            uid,
            f"📧 *New Account Task*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"First Name 📛 = `{account['first_name']}`\n"
            f"Last Name = 🚫\n"
            f"Username 👾 = `{account['username']}`\n"
            f"Password 🔑 = `{account['password']}`\n\n"
            f"✅ Complete the task and click *Done*\n"
            f"💰 Reward: *{TASK_REWARD:.2f}\\$*",
            parse_mode="MarkdownV2",
            reply_markup=task_action_keyboard(),
        )

    # ── Done button ───────────────────────────────────────────────────────────
    def handle_done(bot: telebot.TeleBot, uid: int) -> None:
        account = get_current_task(uid)

        if not account:
            bot.send_message(
                uid,
                "⚠️ No active task found\\. Please start a new task first\\.",
                parse_mode="MarkdownV2",
                reply_markup=main_menu_keyboard(),
            )
            return

        task_id = add_pending_task(uid, account)
        clear_current_task(uid)
        clear_state(uid)
        audit(uid, "task_submitted", f"task_id={task_id}")

        bot.send_message(
            uid,
            "📨 *Task Submitted\\!*\n"
            "━━━━━━━━━━━━━━━\n"
            "Your task is under review\\. ✅\n\n"
            "💰 Balance will be added after verification\\.",
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )

        # Notify owner
        profile = get_profile(uid)
        try:
            bot.send_message(
                OWNER_ID,
                f"📋 *New Task Submission*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 {_escape(profile.get('name', 'N/A'))} \\(`{uid}`\\)\n"
                f"🆔 Task ID: `{task_id}`\n"
                f"📧 {_escape(account.get('username', 'N/A'))}\n\n"
                f"✅ `/approve {task_id}`\n"
                f"❌ `/reject {task_id}`",
                parse_mode="MarkdownV2",
            )
        except Exception:
            pass

        logger.info("Task submitted uid=%s task_id=%s", uid, task_id)

    # ── Cancel button ─────────────────────────────────────────────────────────
    def handle_cancel_task(bot: telebot.TeleBot, uid: int) -> None:
        clear_current_task(uid)
        clear_state(uid)
        audit(uid, "task_cancelled")
        from handlers.main_handler import send_main_menu
        send_main_menu(bot, uid)

    # Expose callables so main_handler can call them
    bot._tasks_handle_tasks_menu    = handle_tasks_menu
    bot._tasks_handle_start_task    = handle_start_task
    bot._tasks_handle_done          = handle_done
    bot._tasks_handle_cancel_task   = handle_cancel_task


def _escape(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in str(text))
      
