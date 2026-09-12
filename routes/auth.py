from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, fetch_one
from services.email_service import send_otp_email
from services.otp_service import can_resend, create_otp, verify_otp as verify_otp_code
from utils.validators import strong_password, valid_email, valid_phone

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
        elif not user["email_verified"]:
            flash("Please verify your email before logging in.", "warning")
        elif user["role"] == "patient" and user["status"] != "Active":
            flash("This account is inactive.", "danger")
        elif user["role"] == "doctor" and (
            not fetch_one("SELECT id FROM doctors WHERE user_id = %s AND status = 'Active'", (user["id"],))
        ):
            flash("This doctor account is inactive.", "danger")
        else:
            if user["role"] in {"patient", "doctor"}:
                session.clear()
                session["pending_login"] = {"user_id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
                try:
                    code = create_otp(user["email"], "login_otp")
                    send_otp_email(user["email"], user["name"], code)
                except Exception:
                    session.clear()
                    flash("We could not send your login OTP. Check SMTP settings and try again.", "danger")
                else:
                    flash("A login OTP was sent to your email.", "success")
                    return redirect(url_for("auth.verify_login_otp"))
            else:
                session.clear()
                session.update(user_id=user["id"], name=user["name"], role=user["role"], email=user["email"])
                return redirect(url_for("admin.dashboard"))
    return render_template("login.html")


@auth_bp.route("/verify-login-otp", methods=["GET", "POST"])
def verify_login_otp():
    pending = session.get("pending_login")
    if not pending:
        flash("Start the login process before verifying an OTP.", "info")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        valid, message = verify_otp_code(pending["email"], request.form.get("otp", "").strip(), "login_otp")
        if valid:
            session.clear()
            session.update(user_id=pending["user_id"], name=pending["name"], role=pending["role"], email=pending["email"])
            target = {"patient": "patient.dashboard", "doctor": "doctor.dashboard"}
            return redirect(url_for(target[pending["role"]]))
        flash(message, "danger")
    return render_template("verify_login_otp.html", email=pending["email"])


@auth_bp.route("/resend-login-otp", methods=["POST"])
def resend_login_otp():
    pending = session.get("pending_login")
    if not pending:
        return redirect(url_for("auth.login"))
    if not can_resend("login_otp"):
        flash("Please wait before requesting another login OTP.", "warning")
        return redirect(url_for("auth.verify_login_otp"))
    try:
        code = create_otp(pending["email"], "login_otp")
        send_otp_email(pending["email"], pending["name"], code)
        flash("A new login OTP was sent.", "success")
    except Exception:
        flash("We could not send a new login OTP. Try again later.", "danger")
    return redirect(url_for("auth.verify_login_otp"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = fetch_one("SELECT * FROM users WHERE email = %s AND role IN ('patient', 'doctor')", (email,))
        if user and user["email_verified"] and user["status"] == "Active":
            session["pending_password_reset"] = {"user_id": user["id"], "email": user["email"], "name": user["name"]}
            try:
                code = create_otp(email, "password_reset_otp")
                send_otp_email(email, user["name"], code)
            except Exception:
                session.pop("pending_password_reset", None)
                session.pop("password_reset_otp", None)
                flash("We could not send the password reset OTP. Check SMTP settings and try again.", "danger")
            else:
                flash("If the account exists, a password reset OTP has been sent.", "success")
                return redirect(url_for("auth.reset_password"))
        else:
            flash("If the account exists, a password reset OTP has been sent.", "success")
    return render_template("forgot_password.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    pending = session.get("pending_password_reset")
    if not pending:
        flash("Start the password reset process first.", "info")
        return redirect(url_for("auth.forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        if not strong_password(password):
            flash("Password must be at least 8 characters and include a letter and number.", "danger")
        elif password != request.form.get("confirm_password", ""):
            flash("Passwords do not match.", "danger")
        else:
            valid, message = verify_otp_code(pending["email"], request.form.get("otp", "").strip(), "password_reset_otp")
            if valid:
                execute("UPDATE users SET password_hash = %s WHERE id = %s", (generate_password_hash(password), pending["user_id"]))
                session.pop("pending_password_reset", None)
                flash("Password reset successfully. You can now log in.", "success")
                return redirect(url_for("auth.login"))
            flash(message, "danger")
    return render_template("reset_password.html", email=pending["email"])


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = request.form
    if request.method == "POST":
        name = form.get("name", "").strip()
        email = form.get("email", "").strip().lower()
        phone = form.get("phone", "").strip()
        password = form.get("password", "")
        confirm = form.get("confirm_password", "")
        errors = []
        if not name:
            errors.append("Full name is required.")
        if not valid_email(email):
            errors.append("Enter a valid email address.")
        if not valid_phone(phone):
            errors.append("Enter a valid phone number.")
        if not strong_password(password):
            errors.append("Password must be at least 8 characters and include a letter and number.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if fetch_one("SELECT id FROM users WHERE email = %s", (email,)):
            errors.append("That email address is already registered.")
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", form=form)
        session["pending_registration"] = {"name": name, "email": email, "phone": phone, "password": password}
        try:
            code = create_otp(email)
            send_otp_email(email, name, code)
        except Exception:
            session.pop("pending_registration", None)
            session.pop("otp", None)
            flash("We could not send the OTP. Check SMTP settings and try again.", "danger")
            return render_template("register.html", form=form)
        flash("A verification OTP was sent to your email.", "success")
        return redirect(url_for("auth.verify_otp"))
    return render_template("register.html")


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending = session.get("pending_registration")
    if not pending:
        flash("Start registration before verifying an email.", "info")
        return redirect(url_for("auth.register"))
    if request.method == "POST":
        code = request.form.get("otp", "").strip()
        valid, message = verify_otp_code(pending["email"], code)
        if valid:
            user_id = execute(
                "INSERT INTO users (name, email, phone, password_hash, role, email_verified) VALUES (%s, %s, %s, %s, 'patient', TRUE)",
                (pending["name"], pending["email"], pending["phone"], generate_password_hash(pending["password"])),
            )
            execute("INSERT INTO patients (user_id) VALUES (%s)", (user_id,))
            session.pop("pending_registration", None)
            flash("Your account is verified. You can now log in.", "success")
            return redirect(url_for("auth.login"))
        flash(message, "danger")
    return render_template("verify_otp.html", email=pending["email"])


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    pending = session.get("pending_registration")
    if not pending:
        return redirect(url_for("auth.register"))
    if not can_resend():
        flash("Please wait before requesting another OTP.", "warning")
        return redirect(url_for("auth.verify_otp"))
    try:
        code = create_otp(pending["email"])
        send_otp_email(pending["email"], pending["name"], code)
        flash("A new OTP was sent.", "success")
    except Exception:
        flash("We could not send a new OTP. Try again later.", "danger")
    return redirect(url_for("auth.verify_otp"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))
