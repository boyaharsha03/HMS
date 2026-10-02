import smtplib
from email.message import EmailMessage

from flask import current_app


def send_otp_email(recipient, name, code):
    username = str(current_app.config.get("MAIL_USERNAME", "")).strip()
    password = str(current_app.config.get("MAIL_PASSWORD", "")).strip()
    if (
        not username
        or not password
        or username.lower().startswith("your_")
        or password.lower().startswith("your_")
        or "gmail_app_password" in password.lower()
    ):
        raise RuntimeError("SMTP username and password are not configured for a real mail account.")

    message = EmailMessage()
    message["Subject"] = "Hospital Management System - Email Verification OTP"
    message["From"] = "carepoint.hms@gmail.com"
    message["To"] = recipient
    message.set_content(
        f"Hello {name},\n\nYour verification OTP is: {code}\n\n"
        f"This OTP is valid for {current_app.config['OTP_EXPIRY_MINUTES']} minutes.\n\n"
        "If you did not request this OTP, please ignore this email.\n\n"
        "Regards,\nHospital Management System"
    )
    try:
        with smtplib.SMTP(current_app.config["MAIL_SERVER"], current_app.config["MAIL_PORT"]) as smtp:
            if current_app.config["MAIL_USE_TLS"]:
                smtp.starttls()
            smtp.login(current_app.config["MAIL_USERNAME"], current_app.config["MAIL_PASSWORD"])
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        current_app.logger.exception("SMTP delivery failed: %s", error)
        raise RuntimeError("SMTP delivery failed. Check your mail settings and app password.") from error

