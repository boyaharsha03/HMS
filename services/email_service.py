import smtplib
from email.message import EmailMessage

from flask import current_app


def send_otp_email(recipient, name, code):
    if not current_app.config["MAIL_USERNAME"] or not current_app.config["MAIL_PASSWORD"]:
        raise RuntimeError("SMTP username and password are not configured")

    message = EmailMessage()
    message["Subject"] = "Hospital Management System - Email Verification OTP"
    message["From"] = current_app.config["MAIL_USERNAME"]
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

