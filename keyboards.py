"""
keyboards.py — All ReplyKeyboardMarkup builders in one place.
"""

from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📋 Tasks"),       KeyboardButton("💰 Wallet"))
    kb.row(KeyboardButton("💸 Withdraw"),    KeyboardButton("🫂 Referral"))
    kb.row(KeyboardButton("🎁 Daily Bonus"), KeyboardButton("👤 Profile"))
    return kb


def tasks_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📧 Create Account - Earn 0.25$"))
    kb.row(KeyboardButton("🔙 Back"))
    return kb


def task_action_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("✅ Done"))
    kb.row(KeyboardButton("❌ Cancel Task"))
    return kb


def back_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🔙 Back"))
    return kb


def withdraw_method_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("Binance ✅"), KeyboardButton("bkash ✅"))
    kb.row(KeyboardButton("🔙 Back"))
    return kb


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

