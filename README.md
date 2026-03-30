# 💎 Earn Farmer Bot

A Telegram bot that lets users earn money by completing simple account-creation
tasks. Built with **pyTelegramBotAPI** and **SQLite**.

---

## Features

| Feature | Description |
|---|---|
| 📧 Tasks | Generate and submit account registrations for review |
| 💰 Wallet | View current balance |
| 💸 Withdraw | Withdraw via Binance (BEP-20) or bkash |
| 🎁 Daily Bonus | Claim a small daily reward every 24 hours |
| 🫂 Referral | Share a link and earn per new user |
| 👤 Profile | View stats and join date |
| 🛡️ Admin panel | Approve/reject tasks, manage balances, ban users |

---

## Quick Start

```bash
# 1. Clone
git clone [github.com](https://github.com/yourname/earn-farmer-bot.git)
cd earn-farmer-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env — set BOT_TOKEN and OWNER_ID

# 4. Run
python main.py
```

---

## Project Structure

```
earn-farmer-bot/
├── main.py              # Entry point
├── config.py            # All constants & env vars
├── database.py          # Schema + all DB helpers
├── keyboards.py         # ReplyKeyboard builders
├── handlers/
│   ├── start.py         # /start + referral
│   ├── admin.py         # Owner commands
│   ├── tasks.py         # Task flow
│   ├── wallet.py        # Wallet display
│   ├── withdrawal.py    # Withdrawal flow
│   ├── bonus.py         # Daily bonus
│   ├── referral.py      # Referral display
│   ├── profile.py       # Profile display
│   └── main_handler.py  # Text message router
├── services/            # (reserved for future business-logic extraction)
├── utils/
│   ├── account_gen.py   # Name/email/password generation
│   ├── validators.py    # Input validation
│   ├── rate_limiter.py  # Sliding-window rate limiting
│   └── logger.py        # Rotating file + console logger
├── migrations/
│   └── migrate.py       # One-time additive schema migration
└── logs/                # Auto-created log files
```

---

## Admin Commands

| Command | Description |
|---|---|
| `/check USER_ID` | View user info |
| `/add USER_ID AMOUNT` | Add balance |
| `/remove USER_ID AMOUNT` | Deduct balance |
| `/set USER_ID AMOUNT` | Set balance to exact value |
| `/pending` | List all tasks awaiting review |
| `/approve TASK_ID` | Approve a task and pay the user |
| `/reject TASK_ID` | Reject a task |
| `/ban USER_ID` | Ban a user |
| `/unban USER_ID` | Unban a user |

---

## Configuration (`config.py`)

| Variable | Default | Description |
|---|---|---|
| `TASK_REWARD` | 0.25 | USD paid per approved task |
| `DAILY_BONUS_AMOUNT` | 0.15 | Daily bonus amount |
| `REFERRAL_BONUS` | 0.10 | Referral reward |
| `MIN_WITHDRAWAL` | 3.00 | Minimum withdrawal threshold |
| `RATE_LIMIT_MAX_MESSAGES` | 20 | Messages per window |
| `RATE_LIMIT_WINDOW_SECONDS` | 60 | Rate-limit window |

---

## Security Notes

- All user-provided text is validated before processing
- Wallet addresses must match BEP-20 format (`0x` + 40 hex chars)
- bkash numbers must match Bangladeshi mobile format
- Referral bonuses are only awarded once per user
- Pending tasks are capped per user to prevent spam
- All balance operations use `ROUND(MAX(0, ...))` to prevent corruption
- A ban system allows the owner to block abusive users
- An audit log records all significant events
- A rate limiter prevents message flooding

---

## License

MIT

