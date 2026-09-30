import os
import resend
from flask import current_app


def send_otp_email(recipient, name, code):
    api_key = os.getenv("RESEND_API_KEY")

    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    resend.api_key = api_key

    expiry_minutes = current_app.config.get("OTP_EXPIRY_MINUTES", 10)

    params = {
        "from": "Hospital Management System <onboarding@resend.dev>",
        "to": [recipient],
        "subject": "Hospital Management System - Email Verification OTP",
        "html": f"""
        <html>
        <body>
            <p>Hello {name},</p>

            <p>Your verification OTP is:</p>

            <h2>{code}</h2>

            <p>
                This OTP is valid for {expiry_minutes} minutes.
            </p>

            <p>
                If you did not request this OTP, please ignore this email.
            </p>

            <p>
                Regards,<br>
                Hospital Management System
            </p>
        </body>
        </html>
        """
    }

    try:
        resend.Emails.send(params)
    except Exception as error:
        current_app.logger.exception(
            "Resend email delivery failed: %s", error
        )
        raise RuntimeError(
            "Email delivery failed. Please check the Resend configuration."
        ) from error