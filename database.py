"""
database.py — All SQLite setup, schema definition, migrations, and
              low-level data-access helpers.

Design notes:
  • Every public function opens and closes its own connection so callers
    never have to manage connection lifetimes.
  • WAL mode + foreign-key enforcement are set per-connection via
    sqlite3's check_same_thread=False (safe because we serialise writes
    inside the Python GIL for single-process bots).
  • Indexes are declared alongside the tables they belong to.
  • Extra tables added vs. original:
      - withdrawal_requests  (audit trail for every withdrawal)
      - task_history         (approved/rejected task log)
      - audit_log            (general event log)
      - rate_limit_log       (per-user request timestamps for rate limiting)
"""

import sqlite3
import time
from config import DB_PATH


# ══════════════════════════════════════════════════════════════════════════════
# CONNECTION
# ══════════════════════════════════════════════════════════════════════════════

def get_conn() -> sqlite3.Connection:
    """Return a thread-safe SQLite connection with WAL and FK support."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")  # wait up to 5 s on lock
    return conn


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMA INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════

def init_db() -> None:
    """Create all tables and indexes if they do not already exist."""
    with get_conn() as conn:
        conn.executescript("""
            -- ── Core user table ──────────────────────────────────────────────
            CREATE TABLE IF NOT EXISTS users (
                uid                 INTEGER PRIMARY KEY,
                name                TEXT    NOT NULL DEFAULT 'User',
                username            TEXT    NOT NULL DEFAULT 'N/A',
                join_date           TEXT    NOT NULL,
                balance             REAL    NOT NULL DEFAULT 0.0
                                    CHECK  (balance >= 0),
                tasks_count         INTEGER NOT NULL DEFAULT 0
                                    CHECK  (tasks_count >= 0),
                withdrawals_count   INTEGER NOT NULL DEFAULT 0
                                    CHECK  (withdrawals_count >= 0),
                referrals_count     INTEGER NOT NULL DEFAULT 0
                                    CHECK  (referrals_count >= 0),
                referrer_id         INTEGER,
                is_banned           INTEGER NOT NULL DEFAULT 0,
                created_at          REAL    NOT NULL DEFAULT (unixepoch()),
                FOREIGN KEY (referrer_id) REFERENCES users(uid)
                    ON DELETE SET NULL
            );

            -- ── Per-user conversation state ───────────────────────────────────
            CREATE TABLE IF NOT EXISTS states (
                uid   INTEGER PRIMARY KEY,
                state TEXT    NOT NULL DEFAULT ''
            );

            -- ── Tasks awaiting owner review ───────────────────────────────────
            CREATE TABLE IF NOT EXISTS pending_tasks (
                task_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                uid          INTEGER NOT NULL,
                first_name   TEXT    NOT NULL,
                last_name    TEXT    NOT NULL,
                email        TEXT    NOT NULL,
                password     TEXT    NOT NULL,
                submitted_at REAL    NOT NULL DEFAULT (unixepoch()),
                FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_pending_tasks_uid
                ON pending_tasks(uid);
            CREATE INDEX IF NOT EXISTS idx_pending_tasks_submitted
                ON pending_tasks(submitted_at);

            -- ── Per-user daily bonus tracking ─────────────────────────────────
            CREATE TABLE IF NOT EXISTS bonus_log (
                uid        INTEGER PRIMARY KEY,
                last_claim REAL    NOT NULL DEFAULT 0,
                FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
            );

            -- ── Global used-email registry ────────────────────────────────────
            CREATE TABLE IF NOT EXISTS used_emails (
                email      TEXT PRIMARY KEY,
                created_at REAL NOT NULL DEFAULT (unixepoch())
            );

            -- ── Task currently being worked on by a user ──────────────────────
            CREATE TABLE IF NOT EXISTS current_tasks (
                uid        INTEGER PRIMARY KEY,
                first_name TEXT    NOT NULL,
                last_name  TEXT    NOT NULL,
                email      TEXT    NOT NULL,
                password   TEXT    NOT NULL,
                started_at REAL    NOT NULL DEFAULT (unixepoch()),
                FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
            );

            -- ── Approved / rejected task history (audit) ─────────────────────
            CREATE TABLE IF NOT EXISTS task_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id     INTEGER NOT NULL,
                uid         INTEGER NOT NULL,
                email       TEXT    NOT NULL,
                action      TEXT    NOT NULL CHECK(action IN ('approved','rejected')),
                acted_by    INTEGER NOT NULL,
                acted_at    REAL    NOT NULL DEFAULT (unixepoch()),
                reward      REAL    NOT NULL DEFAULT 0.0
            );
            CREATE INDEX IF NOT EXISTS idx_task_history_uid
                ON task_history(uid);

            -- ── Withdrawal requests (full audit trail) ────────────────────────
            CREATE TABLE IF NOT EXISTS withdrawal_requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                uid         INTEGER NOT NULL,
                method      TEXT    NOT NULL,
                address     TEXT    NOT NULL,
                amount      REAL    NOT NULL CHECK(amount > 0),
                status      TEXT    NOT NULL DEFAULT 'pending'
                                    CHECK(status IN ('pending','processed','rejected')),
                requested_at REAL   NOT NULL DEFAULT (unixepoch()),
                processed_at REAL,
                FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_withdrawal_uid
                ON withdrawal_requests(uid);
            CREATE INDEX IF NOT EXISTS idx_withdrawal_status
                ON withdrawal_requests(status);

            -- ── General audit / event log ─────────────────────────────────────
            CREATE TABLE IF NOT EXISTS audit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                uid        INTEGER,
                event      TEXT    NOT NULL,
                detail     TEXT,
                created_at REAL    NOT NULL DEFAULT (unixepoch())
            );
            CREATE INDEX IF NOT EXISTS idx_audit_uid
                ON audit_log(uid);
            CREATE INDEX IF NOT EXISTS idx_audit_event
                ON audit_log(event);

            -- ── Per-user rate-limit event timestamps ──────────────────────────
            CREATE TABLE IF NOT EXISTS rate_limit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                uid        INTEGER NOT NULL,
                ts         REAL    NOT NULL DEFAULT (unixepoch()),
                FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_rate_uid_ts
                ON rate_limit_log(uid, ts);
        """)


# ══════════════════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════════════════

def ensure_profile(uid: int, full_name: str = "User", username: str = "N/A") -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (uid, name, username, join_date, balance)
            VALUES (?, ?, ?, ?, 0.0)
            ON CONFLICT(uid) DO UPDATE SET
                name     = excluded.name,
                username = excluded.username
            """,
            (uid, full_name, username, time.strftime("%d %b %Y")),
        )


def get_profile(uid: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE uid = ?", (uid,)
        ).fetchone()
    return dict(row) if row else {}


def get_balance(uid: int) -> float:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT balance FROM users WHERE uid = ?", (uid,)
        ).fetchone()
    return round(row["balance"], 2) if row else 0.0


def set_balance(uid: int, amount: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET balance = ? WHERE uid = ?",
            (round(max(0.0, amount), 2), uid),
        )


def add_balance(uid: int, amount: float) -> None:
    """Atomically add *amount* to a user's balance (floor at 0)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET balance = ROUND(MAX(0, balance + ?), 2) WHERE uid = ?",
            (amount, uid),
        )


def deduct_balance(uid: int, amount: float) -> None:
    """Atomically deduct *amount* from a user's balance (floor at 0)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET balance = ROUND(MAX(0, balance - ?), 2) WHERE uid = ?",
            (amount, uid),
        )


def is_banned(uid: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT is_banned FROM users WHERE uid = ?", (uid,)
        ).fetchone()
    return bool(row["is_banned"]) if row else False


def set_banned(uid: int, banned: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_banned = ? WHERE uid = ?",
            (1 if banned else 0, uid),
        )


# ══════════════════════════════════════════════════════════════════════════════
# STATES
# ══════════════════════════════════════════════════════════════════════════════

def set_state(uid: int, state: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO states (uid, state) VALUES (?, ?) "
            "ON CONFLICT(uid) DO UPDATE SET state = excluded.state",
            (uid, state),
        )


def get_state(uid: int) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT state FROM states WHERE uid = ?", (uid,)
        ).fetchone()
    return row["state"] if row else ""


def clear_state(uid: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM states WHERE uid = ?", (uid,))


# ══════════════════════════════════════════════════════════════════════════════
# CURRENT TASKS
# ══════════════════════════════════════════════════════════════════════════════

def set_current_task(uid: int, account: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO current_tasks (uid, first_name, last_name, email, password, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET
                first_name = excluded.first_name,
                last_name  = excluded.last_name,
                email      = excluded.email,
                password   = excluded.password,
                started_at = excluded.started_at
            """,
            (
                uid,
                account["first_name"],
                account["last_name"],
                account["username"],
                account["password"],
                time.time(),
            ),
        )


def get_current_task(uid: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM current_tasks WHERE uid = ?", (uid,)
        ).fetchone()
    if not row:
        return None
    return {
        "first_name": row["first_name"],
        "last_name":  row["last_name"],
        "username":   row["email"],
        "password":   row["password"],
    }


def clear_current_task(uid: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM current_tasks WHERE uid = ?", (uid,))


# ══════════════════════════════════════════════════════════════════════════════
# PENDING TASKS
# ══════════════════════════════════════════════════════════════════════════════

def add_pending_task(uid: int, account: dict) -> int:
    """Insert a pending task and return its auto-generated task_id."""
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO pending_tasks
                (uid, first_name, last_name, email, password, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                uid,
                account["first_name"],
                account["last_name"],
                account["username"],
                account["password"],
                time.time(),
            ),
        )
        return cur.lastrowid


def get_pending_tasks_for_user(uid: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pending_tasks WHERE uid = ? ORDER BY submitted_at ASC",
            (uid,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_pending_tasks() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM pending_tasks ORDER BY submitted_at ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_pending_task_by_id(task_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM pending_tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
    return dict(row) if row else None


def delete_pending_task(task_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM pending_tasks WHERE task_id = ?", (task_id,))


def count_pending_tasks_for_user(uid: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM pending_tasks WHERE uid = ?", (uid,)
        ).fetchone()
    return row["cnt"] if row else 0


# ══════════════════════════════════════════════════════════════════════════════
# TASK HISTORY
# ══════════════════════════════════════════════════════════════════════════════

def record_task_action(
    task_id: int,
    uid: int,
    email: str,
    action: str,
    acted_by: int,
    reward: float = 0.0,
) -> None:
    """Persist an approved/rejected event to task_history."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO task_history (task_id, uid, email, action, acted_by, acted_at, reward)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, uid, email, action, acted_by, time.time(), reward),
        )


# ══════════════════════════════════════════════════════════════════════════════
# BONUS LOG
# ══════════════════════════════════════════════════════════════════════════════

def can_claim_bonus(uid: int) -> bool:
    from config import DAILY_BONUS_INTERVAL
    with get_conn() as conn:
        row = conn.execute(
            "SELECT last_claim FROM bonus_log WHERE uid = ?", (uid,)
        ).fetchone()
    last = row["last_claim"] if row else 0
    return (time.time() - last) >= DAILY_BONUS_INTERVAL


def time_until_next_bonus(uid: int) -> str:
    from config import DAILY_BONUS_INTERVAL
    with get_conn() as conn:
        row = conn.execute(
            "SELECT last_claim FROM bonus_log WHERE uid = ?", (uid,)
        ).fetchone()
    last      = row["last_claim"] if row else 0
    remaining = DAILY_BONUS_INTERVAL - (time.time() - last)
    if remaining <= 0:
        return "Available now!"
    hours   = int(remaining // 3600)
    minutes = int((remaining % 3600) // 60)
    return f"{hours}h {minutes}m"


def record_bonus_claim(uid: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO bonus_log (uid, last_claim) VALUES (?, ?) "
            "ON CONFLICT(uid) DO UPDATE SET last_claim = excluded.last_claim",
            (uid, time.time()),
        )


# ══════════════════════════════════════════════════════════════════════════════
# USED EMAILS
# ══════════════════════════════════════════════════════════════════════════════

def email_is_used(email: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM used_emails WHERE email = ?", (email,)
        ).fetchone()
    return row is not None


def mark_email_used(email: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO used_emails (email) VALUES (?)", (email,)
        )


# ══════════════════════════════════════════════════════════════════════════════
# WITHDRAWAL REQUESTS
# ══════════════════════════════════════════════════════════════════════════════

def record_withdrawal_request(
    uid: int, method: str, address: str, amount: float
) -> int:
    """Log a withdrawal request and return its ID."""
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO withdrawal_requests (uid, method, address, amount, requested_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (uid, method, address, round(amount, 2), time.time()),
        )
        return cur.lastrowid


# ══════════════════════════════════════════════════════════════════════════════
# AUDIT LOG
# ══════════════════════════════════════════════════════════════════════════════

def audit(uid: int | None, event: str, detail: str = "") -> None:
    """Write a single line to the audit_log table."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_log (uid, event, detail, created_at) VALUES (?, ?, ?, ?)",
            (uid, event, detail, time.time()),
        )


# ══════════════════════════════════════════════════════════════════════════════
# RATE LIMITING
# ══════════════════════════════════════════════════════════════════════════════

def record_message(uid: int) -> None:
    """Record that *uid* sent a message right now."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO rate_limit_log (uid, ts) VALUES (?, ?)",
            (uid, time.time()),
        )


def count_messages_in_window(uid: int, window_seconds: int) -> int:
    """Count messages from *uid* within the last *window_seconds* seconds."""
    cutoff = time.time() - window_seconds
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM rate_limit_log WHERE uid = ? AND ts >= ?",
            (uid, cutoff),
        ).fetchone()
    return row["cnt"] if row else 0


def purge_old_rate_limit_rows(window_seconds: int) -> None:
    """Delete rate-limit rows older than *window_seconds* to keep the table small."""
    cutoff = time.time() - window_seconds
    with get_conn() as conn:
        conn.execute("DELETE FROM rate_limit_log WHERE ts < ?", (cutoff,))


# ══════════════════════════════════════════════════════════════════════════════
# REFERRAL
# ══════════════════════════════════════════════════════════════════════════════

def set_referrer(uid: int, referrer_id: int) -> None:
    """Set the referrer for *uid* and increment referrer's counter atomically."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET referrer_id = ? WHERE uid = ? AND referrer_id IS NULL",
            (referrer_id, uid),
        )
        conn.execute(
            "UPDATE users SET referrals_count = referrals_count + 1 WHERE uid = ?",
            (referrer_id,),
        )
          
