import re
from config import (
    BINANCE_ADDRESS_MIN_LEN,
    BINANCE_ADDRESS_MAX_LEN,
    BKASH_NUMBER_MIN_LEN,
    BKASH_NUMBER_MAX_LEN,
)


def is_valid_binance_address(address: str) -> bool:
    """
    Accepts BEP-20 (BSC) addresses.
    Standard EVM address: 0x followed by 40 hex chars.
    Also allows raw 42-char hex strings without 0x prefix for flexibility.
    """
    address = address.strip()
    if not (BINANCE_ADDRESS_MIN_LEN <= len(address) <= BINANCE_ADDRESS_MAX_LEN):
        return False
    # Standard 0x EVM address
    if re.fullmatch(r"0x[0-9a-fA-F]{40}", address):
        return True
    return False


def is_valid_bkash_number(number: str) -> bool:
    """
    bkash numbers are Bangladeshi mobile numbers.
    Accepted formats: 01XXXXXXXXX (11 digits) or +8801XXXXXXXXX (14 chars).
    """
    number = number.strip()
    # Strip optional country code
    if number.startswith("+880"):
        number = "0" + number[4:]
    if not re.fullmatch(r"01[3-9]\d{8}", number):
        return False
    if not (BKASH_NUMBER_MIN_LEN <= len(number.replace("+", "")) <= BKASH_NUMBER_MAX_LEN):
        return False
    return True


def sanitise_text(text: str, max_len: int = 200) -> str:
    """Strip leading/trailing whitespace and truncate to *max_len* chars."""
    return text.strip()[:max_len]
  
