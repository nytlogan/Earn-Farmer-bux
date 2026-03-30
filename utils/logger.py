"""
utils/logger.py — Centralised logging configuration.
Import `logger` from here in every module.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "bot.log")

os.makedirs(LOG_DIR, exist_ok=True)

_fmt = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file_handler.setFormatter(_fmt)

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_fmt)

logger = logging.getLogger("earn_farmer")
logger.setLevel(logging.INFO)
logger.addHandler(_file_handler)
logger.addHandler(_stream_handler)

