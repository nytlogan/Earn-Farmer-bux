"""
main.py — Entry point.

Registers all handler modules then starts long-polling.
"""

import telebot

from config import BOT_TOKEN
from database import init_db
from utils.logger import logger
from migrations.migrate import run_migrations

# ── Handler modules ───────────────────────────────────────────────────────────
from handlers import start, admin, tasks, main_handler

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)


def main() -> None:
    logger.info("Initialising database…")
    init_db()
    run_migrations()

    logger.info("Registering handlers…")
    start.register(bot)     # /start
    admin.register(bot)     # /check /add /remove /set /pending /approve /reject /ban /unban
    tasks.register(bot)     # task logic (attaches callables to bot object)
    main_handler.register(bot)  # catch-all text router — must be last

    logger.info("💎 Earn Farmer Bot is running…")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)


if __name__ == "__main__":
    main()
  
