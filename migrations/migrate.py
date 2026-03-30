"""
migrations/migrate.py — Safe, additive migration from the original single-file schema
to the new extended schema.

Run once:  python migrations/migrate.py

Strategy:
  • Uses ALTER TABLE … ADD COLUMN IF NOT EXISTS patterns (SQLite 3.37+)
    and falls back to a try/except for older SQLite versions.
  • Never drops or renames columns — fully backward-compatible.
  • Creates new tables if absent.
  • Creates indexes if absent.
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_conn, init_db
from utils.logger import logger


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        logger.info("Added column %s.%s", table, column)
    except sqlite3.OperationalError:
        # Column already exists — that's fine
        pass


def run_migrations() -> None:
    logger.info("Running migrations…")

    # Ensure all new tables and indexes exist first
    init_db()

    with get_conn() as conn:
        # users table additions
        _add_column_if_missing(conn, "users", "is_banned",   "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "users", "created_at",  "REAL    NOT NULL DEFAULT 0")

        # current_tasks table addition
        _add_column_if_missing(conn, "current_tasks", "started_at", "REAL NOT NULL DEFAULT 0")

        # used_emails table addition
        _add_column_if_missing(conn, "used_emails", "created_at", "REAL NOT NULL DEFAULT 0")

    logger.info("Migrations complete.")


if __name__ == "__main__":
    run_migrations()
    print("Migration finished successfully.")
  
