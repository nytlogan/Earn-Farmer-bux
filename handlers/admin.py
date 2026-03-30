"""
handlers/admin.py — Owner-only admin commands:
    /check, /add, /addbalance, /remove, /set, /pending, /approve, /reject, /ban, /unban
"""

import time
import telebot

from config import OWNER_ID, TASK_REWARD
from database import (
    get_profile,
    get_balance,
    add_balance,
    deduct_balance,
    set_balance,
    ensure_profile,
    get_all_pending_tasks,
    get_pending_tasks_for_user,
    get_pending_task_by_id,
    delete_pending_task,
    record_task_action,
    get_conn,
    set_banned,
    audit,
)
from keyboards import main_menu_keyboard
from utils.logger import logger


def register(bot: telebot.TeleBot) -> None:

    # ── Guard ─────────────────────────────────────────────────────────────────
    def owner_only(message) -> bool:
        if message.from_user.id != OWNER_ID:
            try:
                bot.send_message(message.chat.id, "⛔ You are not authorized.")
            except Exception:
                pass
            return False
        return True

    def parse_uid_amount(parts, message, require_amount=True):
        try:
            target_uid = int(parts[1])
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "❌ Invalid USER\\_ID\\.", parse_mode="MarkdownV2")
            return None, None

        amount = None
        if require_amount:
            try:
                amount = float(parts[2])
                if amount < 0:
                    raise ValueError
            except (IndexError, ValueError):
                bot.send_message(
                    message.chat.id,
                    "❌ Invalid AMOUNT\\. Must be a positive number\\.",
                    parse_mode="MarkdownV2",
                )
                return None, None

        return target_uid, amount

    # ── /check USER_ID ────────────────────────────────────────────────────────
    @bot.message_handler(commands=["check"])
    def cmd_check(message):
        if not owner_only(message):
            return
        parts = message.text.split()
        target_uid, _ = parse_uid_amount(parts, message, require_amount=False)
        if target_uid is None:
            return

        profile = get_profile(target_uid)
        if not profile:
            bot.send_message(
                message.chat.id,
                f"❌ User `{target_uid}` not found\\.",
                parse_mode="MarkdownV2",
            )
            return

        pending_count = len(get_pending_tasks_for_user(target_uid))
        bot.send_message(
            message.chat.id,
            f"👤 *User Info*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🆔 User ID: `{target_uid}`\n"
            f"📛 Name: {_escape(profile.get('name', 'N/A'))}\n"
            f"💰 Balance: *{profile.get('balance', 0):.2f}\\$*\n"
            f"✅ Tasks Done: *{profile.get('tasks_count', 0)}*\n"
            f"💸 Withdrawals: *{profile.get('withdrawals_count', 0)}*\n"
            f"👥 Referrals: *{profile.get('referrals_count', 0)}*\n"
            f"⏳ Pending Tasks: *{pending_count}*\n"
            f"🚫 Banned: *{'Yes' if profile.get('is_banned') else 'No'}*",
            parse_mode="MarkdownV2",
        )

    # ── /add USER_ID AMOUNT ───────────────────────────────────────────────────
    @bot.message_handler(commands=["add", "addbalance"])
    def cmd_add_balance(message):
        if not owner_only(message):
            return
        parts = message.text.split()
        target_uid, amount = parse_uid_amount(parts, message)
        if target_uid is None:
            return

        ensure_profile(target_uid)
        add_balance(target_uid, amount)
        new_bal = get_balance(target_uid)
        audit(OWNER_ID, "admin_add_balance", f"uid={target_uid} amount={amount:.2f}")

        bot.send_message(
            message.chat.id,
            f"✅ Added *{amount:.2f}\\$* to `{target_uid}`\\.\n"
            f"💰 New Balance: *{new_bal:.2f}\\$*",
            parse_mode="MarkdownV2",
        )
        try:
            bot.send_message(
                target_uid,
                f"🎉 *Balance Updated\\!*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💰 Added: *\\+{amount:.2f}\\$*\n"
                f"💎 New Balance: *{new_bal:.2f}\\$*",
                parse_mode="MarkdownV2",
            )
        except Exception:
            pass

    # ── /remove USER_ID AMOUNT ────────────────────────────────────────────────
    @bot.message_handler(commands=["remove"])
    def cmd_remove_balance(message):
        if not owner_only(message):
            return
        parts = message.text.split()
        target_uid, amount = parse_uid_amount(parts, message)
        if target_uid is None:
            return

        if not get_profile(target_uid):
            bot.send_message(
                message.chat.id,
                f"❌ User `{target_uid}` not found\\.",
                parse_mode="MarkdownV2",
            )
            return

        old_bal = get_balance(target_uid)
        deduct_balance(target_uid, amount)
        new_bal = get_balance(target_uid)
        audit(OWNER_ID, "admin_remove_balance", f"uid={target_uid} amount={amount:.2f}")

        bot.send_message(
            message.chat.id,
            f"✅ Removed *{amount:.2f}\\$* from `{target_uid}`\\.\n"
            f"💰 Old: *{old_bal:.2f}\\$* → New: *{new_bal:.2f}\\$*",
            parse_mode="MarkdownV2",
        )
        try:
            bot.send_message(
                target_uid,
                f"⚠️ *Balance Updated*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💸 Deducted: *\\-{amount:.2f}\\$*\n"
                f"💎 New Balance: *{new_bal:.2f}\\$*",
                parse_mode="MarkdownV2",
            )
        except Exception:
            pass

    # ── /set USER_ID AMOUNT ───────────────────────────────────────────────────
    @bot.message_handler(commands=["set"])
    def cmd_set_balance(message):
        if not owner_only(message):
            return
        parts = message.text.split()
        target_uid, amount = parse_uid_amount(parts, message)
        if target_uid is None:
            return

        if not get_profile(target_uid):
            bot.send_message(
                message.chat.id,
                f"❌ User `{target_uid}` not found\\.",
                parse_mode="MarkdownV2",
            )
            return

        set_balance(target_uid, amount)
        audit(OWNER_ID, "admin_set_balance", f"uid={target_uid} amount={amount:.2f}")

        bot.send_message(
            message.chat.id,
            f"✅ Balance set to *{amount:.2f}\\$* for `{target_uid}`\\.",
            parse_mode="MarkdownV2",
        )
        try:
            bot.send_message(
                target_uid,
                f"💎 *Balance Updated*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"Your balance was set to *{amount:.2f}\\$*\\.",
                parse_mode="MarkdownV2",
            )
        except Exception:
            pass

    # ── /pending ──────────────────────────────────────────────────────────────
    @bot.message_handler(commands=["pending"])
    def cmd_pending(message):
        if not owner_only(message):
            return

        tasks = get_all_pending_tasks()
        if not tasks:
            bot.send_message(message.chat.id, "✅ No pending tasks right now.")
            return

        lines = ["📋 *Pending Tasks*\n━━━━━━━━━━━━━━━"]
        for i, task in enumerate(tasks, 1):
            uid      = task["uid"]
            profile  = get_profile(uid)
            sub_time = time.strftime(
                "%d %b %Y %H:%M", time.localtime(task["submitted_at"])
            )
            lines.append(
                f"\n*{i}\\.* 👤 {_escape(profile.get('name', 'N/A'))} \\(`{uid}`\\)\n"
                f"   🆔 Task ID: `{task['task_id']}`\n"
                f"   📧 {_escape(task['email'])}\n"
                f"   🕐 {_escape(sub_time)}\n"
                f"   ✅ `/approve {task['task_id']}`  "
                f"❌ `/reject {task['task_id']}`"
            )

        full_text = "\n".join(lines)
        if len(full_text) <= 4096:
            bot.send_message(message.chat.id, full_text, parse_mode="MarkdownV2")
        else:
            chunk = lines[0]
            for line in lines[1:]:
                if len(chunk) + len(line) > 4000:
                    bot.send_message(
                        message.chat.id, chunk, parse_mode="MarkdownV2"
                    )
                    chunk = line
                else:
                    chunk += "\n" + line
            if chunk:
                bot.send_message(
                    message.chat.id, chunk, parse_mode="MarkdownV2"
                )

    # ── /approve TASK_ID ──────────────────────────────────────────────────────
    @bot.message_handler(commands=["approve"])
    def cmd_approve(message):
        if not owner_only(message):
            return
        parts = message.text.split()
        task_id, _ = parse_uid_amount(parts, message, require_amount=False)
        if task_id is None:
            return

        task = get_pending_task_by_id(task_id)
        if not task:
            bot.send_message(
                message.chat.id,
                f"❌ No pending task found with ID `{task_id}`\\.",
                parse_mode="MarkdownV2",
            )
            return

        uid = task["uid"]
        delete_pending_task(task_id)
        add_balance(uid, TASK_REWARD)
        with get_conn() as conn:
            conn.execute(
                "UPDATE users SET tasks_count = tasks_count + 1 WHERE uid = ?",
                (uid,),
            )
        record_task_action(task_id, uid, task["email"], "approved", OWNER_ID, TASK_REWARD)
        audit(OWNER_ID, "task_approved", f"task_id={task_id} uid={uid}")

        bot.send_message(
            message.chat.id,
            f"✅ Task `{task_id}` approved for `{uid}`\\.\n"
            f"💰 Credited *{TASK_REWARD:.2f}\\$*\\.",
            parse_mode="MarkdownV2",
        )
        try:
            bot.send_message(
                uid,
                f"✅ *Task Approved\\!*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💰 *\\+{TASK_REWARD:.2f}\\$* has been added to your balance\\!\n"
                f"💎 New Balance: *{get_balance(uid):.2f}\\$*",
                parse_mode="MarkdownV2",
                reply_markup=main_menu_keyboard(),
            )
        except Exception:
            pass
        logger.info("Task %s approved for uid=%s", task_id, uid)

    # ── /reject TASK_ID ───────────────────────────────────────────────────────
    @bot.message_handler(commands=["reject"])
    def cmd_reject(message):
        if not owner_only(message):
            return
        parts = message.text.split()
        task_id, _ = parse_uid_amount(parts, message, require_amount=False)
        if task_id is None:
            return

        task = get_pending_task_by_id(task_id)
        if not task:
            bot.send_message(
                message.chat.id,
                f"❌ No pending task found with ID `{task_id}`\\.",
                parse_mode="MarkdownV2",
            )
            return

        uid = task["uid"]
        delete_pending_task(task_id)
        record_task_action(task_id, uid, task["email"], "rejected", OWNER_ID, 0.0)
        audit(OWNER_ID, "task_rejected", f"task_id={task_id} uid={uid}")

        bot.send_message(
            message.chat.id,
            f"❌ Task `{task_id}` rejected for `{uid}`\\.",
            parse_mode="MarkdownV2",
        )
        try:
            bot.send_message(
                uid,
                "❌ *Task Rejected*\n"
                "━━━━━━━━━━━━━━━\n"
                "Your submission was not approved\\.\n"
                "Please try again carefully\\. 🙏",
                parse_mode="MarkdownV2",
                reply_markup=main_menu_keyboard(),
            )
        except Exception:
            pass
        logger.info("Task %s rejected for uid=%s", task_id, uid)

    # ── /ban USER_ID ──────────────────────────────────────────────────────────
    @bot.message_handler(commands=["ban"])
    def cmd_ban(message):
        if not owner_only(message):
            return
        parts = message.text.split()
        target_uid, _ = parse_uid_amount(parts, message, require_amount=False)
        if target_uid is None:
            return

        set_banned(target_uid, True)
        audit(OWNER_ID, "admin_ban", f"uid={target_uid}")
        bot.send_message(
            message.chat.id,
            f"🚫 User `{target_uid}` has been banned\\.",
            parse_mode="MarkdownV2",
        )

    # ── /unban USER_ID ────────────────────────────────────────────────────────
    @bot.message_handler(commands=["unban"])
    def cmd_unban(message):
        if not owner_only(message):
            return
        parts = message.text.split()
        target_uid, _ = parse_uid_amount(parts, message, require_amount=False)
        if target_uid is None:
            return

        set_banned(target_uid, False)
        audit(OWNER_ID, "admin_unban", f"uid={target_uid}")
        bot.send_message(
            message.chat.id,
            f"✅ User `{target_uid}` has been unbanned\\.",
            parse_mode="MarkdownV2",
        )


def _escape(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in str(text))
      
