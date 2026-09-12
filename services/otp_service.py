import hashlib
import secrets
from datetime import datetime, timedelta

from flask import current_app, session


def create_otp(email, session_key="otp"):
    code = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.utcnow()
    session[session_key] = {
        "email": email.lower(),
        "hash": hashlib.sha256(code.encode()).hexdigest(),
        "expires_at": (now + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])).isoformat(),
        "sent_at": now.isoformat(),
    }
    return code


def can_resend(session_key="otp"):
    otp = session.get(session_key)
    if not otp:
        return True
    sent_at = datetime.fromisoformat(otp["sent_at"])
    return datetime.utcnow() - sent_at >= timedelta(seconds=current_app.config["OTP_RESEND_SECONDS"])


def verify_otp(email, code, session_key="otp"):
    otp = session.get(session_key)
    if not otp or otp.get("email") != email.lower():
        return False, "No active verification request was found."
    if datetime.utcnow() > datetime.fromisoformat(otp["expires_at"]):
        session.pop(session_key, None)
        return False, "That OTP has expired. Please request a new one."
    if not secrets.compare_digest(otp["hash"], hashlib.sha256(code.encode()).hexdigest()):
        return False, "The OTP is incorrect."
    session.pop(session_key, None)
    return True, "Email verified."
