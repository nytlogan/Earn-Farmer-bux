"""
config.py — Centralised configuration loaded from environment variables.
All constants that drive bot behaviour live here.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
OWNER_ID: int  = int(os.environ.get("OWNER_ID", "0"))

if not BOT_TOKEN:
    sys.exit("[FATAL] BOT_TOKEN is not set. Check your .env file.")

if OWNER_ID == 0:
    sys.exit("[FATAL] OWNER_ID is not set or is 0. Check your .env file.")

# ── Rewards & limits ─────────────────────────────────────────────────────────
TASK_REWARD: float          = 0.25
DAILY_BONUS_AMOUNT: float   = 0.15
REFERRAL_BONUS: float       = 0.10
DAILY_BONUS_INTERVAL: int   = 86_400   # seconds (24 h)
MIN_WITHDRAWAL: float       = 3.00

# ── Storage ──────────────────────────────────────────────────────────────────
DB_PATH: str = "bot_data.db"

# ── Rate limiting ─────────────────────────────────────────────────────────────
# Maximum messages a user may send within the sliding window
RATE_LIMIT_MAX_MESSAGES: int    = 20
RATE_LIMIT_WINDOW_SECONDS: int  = 60

# ── Wallet / address validation ───────────────────────────────────────────────
BINANCE_ADDRESS_MIN_LEN: int = 26
BINANCE_ADDRESS_MAX_LEN: int = 62
BKASH_NUMBER_MIN_LEN: int   = 11
BKASH_NUMBER_MAX_LEN: int   = 14

# ── Account-generation corpus ─────────────────────────────────────────────────
FIRST_NAMES: list[str] = [
    "Alex", "Jordan", "Morgan", "Casey", "Riley", "Taylor", "Drew", "Avery",
    "Blake", "Cameron", "Dakota", "Emerson", "Finley", "Hayden", "Jamie",
    "Kendall", "Logan", "Marlowe", "Nolan", "Oakley", "Parker", "Quinn",
    "Reese", "Skyler", "Tristan", "Uma", "Valentina", "Wesley", "Xander", "Yara",
]

LAST_NAMES: list[str] = [
    "Hunt", "Cole", "Reed", "Stone", "Banks", "Fox", "Hart", "Lane",
    "Nash", "Park", "Reid", "Shaw", "Voss", "Wade", "York", "Zane",
    "Cross", "Drake", "Flynn", "Grant", "Hayes", "Knox", "Miles", "Pierce",
    "Rhodes", "Scott", "Todd", "Urban", "Vance", "Wells",
]

EMAIL_DOMAINS: list[str] = ["gmail.com"]

