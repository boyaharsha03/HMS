from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import execute, fetch_all, fetch_one
from utils.decorators import role_required
from utils.validators import parse_date, valid_phone

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


@patient_bp.route("/dashboard")
@role_required("patient")
def dashboard():
    patient = fetch_one("SELECT id FROM patients WHERE user_id = %s", (session["user_id"],))
    stats = fetch_one(
        """SELECT COUNT(*) total, SUM(status IN ('Pending','Accepted')) upcoming,
                  SUM(status = 'Completed') completed, SUM(status = 'Cancelled') cancelled
           FROM appointments WHERE patient_id = %s""", (patient["id"],)
    )
    upcoming = fetch_all(
        """SELECT a.*, u.name doctor_name, d.specialization, dep.name department
           FROM appointments a JOIN doctors d ON d.id = a.doctor_id JOIN users u ON u.id = d.user_id
           LEFT JOIN departments dep ON dep.id = d.department_id
           WHERE a.patient_id = %s AND a.appointment_date >= CURDATE()
           AND a.status IN ('Pending','Accepted') ORDER BY a.appointment_date, a.appointment_time LIMIT 5""",
        (patient["id"],),
    )
    doctors = fetch_all(
        """SELECT d.id, u.name, d.specialization, d.experience, dep.name department
           FROM doctors d
           JOIN users u ON u.id = d.user_id
           LEFT JOIN departments dep ON dep.id = d.department_id
           WHERE d.status = 'Active' AND u.status = 'Active'
           ORDER BY u.name LIMIT 6"""
    )
    for doctor in doctors:
        doctor["availability"] = fetch_all(
            """SELECT day_of_week, start_time, end_time
               FROM doctor_availability
               WHERE doctor_id = %s AND status = 'Active'
            ORDER BY CASE day_of_week
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7 END, start_time""",
            (doctor["id"],),
        )
    return render_template("patient/dashboard.html", stats=stats, upcoming=upcoming, doctors=doctors)


@patient_bp.route("/profile", methods=["GET", "POST"])
@role_required("patient")
def profile():
    patient = fetch_one("SELECT u.*, p.* FROM users u JOIN patients p ON p.user_id = u.id WHERE u.id = %s", (session["user_id"],))
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        if not valid_phone(phone):
            flash("Enter a valid phone number.", "danger")
        else:
            execute("UPDATE users SET name = %s, phone = %s WHERE id = %s", (request.form.get("name", "").strip(), phone, session["user_id"]))
            execute("UPDATE patients SET date_of_birth = NULLIF(%s, ''), gender = %s, address = %s WHERE user_id = %s", (request.form.get("date_of_birth", ""), request.form.get("gender", ""), request.form.get("address", "").strip(), session["user_id"]))
            session["name"] = request.form.get("name", "").strip()
            flash("Profile updated.", "success")
            return redirect(url_for("patient.profile"))
    return render_template("patient/profile.html", patient=patient)


@patient_bp.route("/doctors")
@role_required("patient")
def doctors():
    search = request.args.get("search", "").strip()
    doctors = fetch_all(
        """SELECT d.id, u.name, d.specialization, d.qualification, d.experience,
                  d.consultation_fee, d.profile_description, dep.name department
           FROM doctors d JOIN users u ON u.id = d.user_id LEFT JOIN departments dep ON dep.id = d.department_id
           WHERE d.status = 'Active' AND (u.name LIKE %s OR d.specialization LIKE %s OR dep.name LIKE %s)
           ORDER BY u.name""", (f"%{search}%", f"%{search}%", f"%{search}%"),
    )
    return render_template("patient/doctors.html", doctors=doctors, search=search)


@patient_bp.route("/doctor/<int:doctor_id>")
@role_required("patient")
def doctor_detail(doctor_id):
    doctor = fetch_one(
        """SELECT d.*, u.name, dep.name department FROM doctors d JOIN users u ON u.id = d.user_id
           LEFT JOIN departments dep ON dep.id = d.department_id WHERE d.id = %s AND d.status = 'Active'""", (doctor_id,)
    )
    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for("patient.doctors"))
    availability = fetch_all("SELECT * FROM doctor_availability WHERE doctor_id = %s AND status = 'Active' ORDER BY day_of_week, start_time", (doctor_id,))
    return render_template("patient/doctor_detail.html", doctor=doctor, availability=availability)


@patient_bp.route("/book-appointment", methods=["GET", "POST"])
@role_required("patient")
def book_appointment():
    doctors = fetch_all("SELECT d.id, u.name, d.specialization FROM doctors d JOIN users u ON u.id = d.user_id WHERE d.status = 'Active' ORDER BY u.name")
    if request.method == "POST":
        doctor_id = request.form.get("doctor_id", type=int)
        appointment_date = parse_date(request.form.get("appointment_date"))
        appointment_time = request.form.get("appointment_time", "")
        reason = request.form.get("reason", "").strip()
        if not doctor_id or not appointment_date or appointment_date < date.today() or not appointment_time:
            flash("Choose a valid future date, doctor, and time.", "danger")
        else:
            patient = fetch_one("SELECT id FROM patients WHERE user_id = %s", (session["user_id"],))
            slot = fetch_one("""SELECT id FROM doctor_availability WHERE doctor_id = %s AND day_of_week = DAYNAME(%s) AND start_time <= %s AND end_time > %s AND status = 'Active'""", (doctor_id, appointment_date, appointment_time, appointment_time))
            booked = fetch_one("SELECT id FROM appointments WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s AND status NOT IN ('Cancelled','Rejected')", (doctor_id, appointment_date, appointment_time))
            if not slot:
                flash("The doctor is not available at that time.", "danger")
            elif booked:
                flash("That time slot has already been booked.", "danger")
            else:
                execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason) VALUES (%s, %s, %s, %s, %s)", (patient["id"], doctor_id, appointment_date, appointment_time, reason))
                flash("Appointment booked successfully.", "success")
                return redirect(url_for("patient.appointments"))
    return render_template("patient/book_appointment.html", doctors=doctors, min_date=date.today().isoformat())


@patient_bp.route("/appointments")
@role_required("patient")
def appointments():
    patient = fetch_one("SELECT id FROM patients WHERE user_id = %s", (session["user_id"],))
    rows = fetch_all("""SELECT a.*, u.name doctor_name, d.specialization, dep.name department FROM appointments a JOIN doctors d ON d.id = a.doctor_id JOIN users u ON u.id = d.user_id LEFT JOIN departments dep ON dep.id = d.department_id WHERE a.patient_id = %s ORDER BY a.appointment_date DESC, a.appointment_time DESC""", (patient["id"],))
    return render_template("patient/appointments.html", appointments=rows)


@patient_bp.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
@role_required("patient")
def cancel_appointment(appointment_id):
    patient = fetch_one("SELECT id FROM patients WHERE user_id = %s", (session["user_id"],))
    execute("UPDATE appointments SET status = 'Cancelled' WHERE id = %s AND patient_id = %s AND status IN ('Pending','Accepted')", (appointment_id, patient["id"]))
    flash("Appointment cancelled.", "success")
    return redirect(url_for("patient.appointments"))
