import re
from datetime import date


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+()\-\s]{7,20}$")


def valid_email(value):
    return bool(EMAIL_RE.match(value or ""))


def valid_phone(value):
    return bool(PHONE_RE.match(value or ""))


def strong_password(value):
    return bool(value and len(value) >= 8 and re.search(r"[A-Za-z]", value) and re.search(r"\d", value))


def parse_date(value):
    try:
        parsed = date.fromisoformat(value)
        return parsed
    except (TypeError, ValueError):
        return None
