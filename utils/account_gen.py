import random
import string
import time

from config import FIRST_NAMES, LAST_NAMES, EMAIL_DOMAINS
from database import email_is_used, mark_email_used, get_pending_tasks_for_user


def generate_password(length: int = 12) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*"),
    ]
    pwd += random.choices(chars, k=length - 4)
    random.shuffle(pwd)
    return "".join(pwd)


def generate_unique_email(first: str, last: str) -> str:
    for _ in range(50):
        style  = random.randint(1, 4)
        num    = random.randint(10, 9999)
        sep    = random.choice([".", "_", "-"])
        domain = random.choice(EMAIL_DOMAINS)

        if style == 1:
            local = f"{first.lower()}{sep}{last.lower()}{num}"
        elif style == 2:
            local = f"{first.lower()}{num}"
        elif style == 3:
            local = f"{last.lower()}{sep}{first.lower()[:3]}{num}"
        else:
            local = f"{first.lower()[0]}{last.lower()}{num}"

        email = f"{local}@{domain}"
        if not email_is_used(email):
            mark_email_used(email)
            return email

    # Fallback — virtually guaranteed unique via timestamp
    email = f"{first.lower()}{last.lower()}{int(time.time())}@gmail.com"
    mark_email_used(email)
    return email


def generate_account(uid: int) -> dict:
    """
    Generate a fresh account whose email has not been submitted by this
    user before.  Checks both the global used_emails table and the user's
    own pending_tasks history.
    """
    rows        = get_pending_tasks_for_user(uid)
    user_emails = {r["email"] for r in rows}

    for _ in range(20):
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        email = generate_unique_email(first, last)
        if email not in user_emails:
            return {
                "first_name": first,
                "last_name":  last,
                "username":   email,
                "password":   generate_password(),
            }

    # Last resort
    first = random.choice(FIRST_NAMES)
    last  = random.choice(LAST_NAMES)
    return {
        "first_name": first,
        "last_name":  last,
        "username":   generate_unique_email(first, last),
        "password":   generate_password(),
}
  
