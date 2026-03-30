from database import count_messages_in_window, record_message, purge_old_rate_limit_rows
from config import RATE_LIMIT_MAX_MESSAGES, RATE_LIMIT_WINDOW_SECONDS
from utils.logger import logger


def check_rate_limit(uid: int) -> bool:
    """
    Record the incoming message and return True if the user is within limits,
    False if they have exceeded the allowed rate.
    """
    # Periodically prune old rows (1-in-50 chance per call to avoid every-call overhead)
    import random
    if random.randint(1, 50) == 1:
        purge_old_rate_limit_rows(RATE_LIMIT_WINDOW_SECONDS)

    record_message(uid)
    count = count_messages_in_window(uid, RATE_LIMIT_WINDOW_SECONDS)

    if count > RATE_LIMIT_MAX_MESSAGES:
        logger.warning("Rate limit exceeded for uid=%s (count=%s)", uid, count)
        return False
    return True
  
