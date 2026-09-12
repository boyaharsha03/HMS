from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db import execute, fetch_all, fetch_one
from utils.decorators import role_required

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")


def current_doctor():
    return fetch_one("SELECT d.*, u.name, u.email, u.phone, dep.name department FROM doctors d JOIN users u ON u.id = d.user_id LEFT JOIN departments dep ON dep.id = d.department_id WHERE d.user_id = %s", (session["user_id"],))


@doctor_bp.route("/dashboard")
@role_required("doctor")
def dashboard():
    doctor = current_doctor()
    stats = fetch_one("""SELECT COUNT(*) total, SUM(status = 'Pending') pending, SUM(status = 'Completed') completed, COUNT(DISTINCT patient_id) patients FROM appointments WHERE doctor_id = %s""", (doctor["id"],))
    today = fetch_all("""SELECT a.*, u.name patient_name, p.phone FROM appointments a JOIN patients pt ON pt.id = a.patient_id JOIN users u ON u.id = pt.user_id JOIN users p ON p.id = pt.user_id WHERE a.doctor_id = %s AND a.appointment_date = CURDATE() ORDER BY a.appointment_time""", (doctor["id"],))
    return render_template("doctor/dashboard.html", doctor=doctor, stats=stats, appointments=today)


@doctor_bp.route("/appointments")
@role_required("doctor")
def appointments():
    doctor = current_doctor()
    rows = fetch_all("""SELECT a.*, u.name patient_name, u.email patient_email, u.phone patient_phone, p.date_of_birth, p.gender, p.address FROM appointments a JOIN patients p ON p.id = a.patient_id JOIN users u ON u.id = p.user_id WHERE a.doctor_id = %s ORDER BY a.appointment_date DESC, a.appointment_time DESC""", (doctor["id"],))
    return render_template("doctor/appointments.html", appointments=rows)


@doctor_bp.route("/appointments/<int:appointment_id>/<action>", methods=["POST"])
@role_required("doctor")
def update_appointment(appointment_id, action):
    doctor = current_doctor()
    status_map = {"accept": "Accepted", "reject": "Rejected", "complete": "Completed"}
    if action in status_map:
        execute("UPDATE appointments SET status = %s WHERE id = %s AND doctor_id = %s", (status_map[action], appointment_id, doctor["id"]))
        flash(f"Appointment {status_map[action].lower()}.", "success")
    return redirect(url_for("doctor.appointments"))


@doctor_bp.route("/availability", methods=["GET", "POST"])
@role_required("doctor")
def availability():
    doctor = current_doctor()
    if request.method == "POST":
        execute("INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time) VALUES (%s, %s, %s, %s)", (doctor["id"], request.form.get("day_of_week"), request.form.get("start_time"), request.form.get("end_time")))
        flash("Availability added.", "success")
    slots = fetch_all("SELECT * FROM doctor_availability WHERE doctor_id = %s ORDER BY day_of_week, start_time", (doctor["id"],))
    return render_template("doctor/availability.html", availability=slots)


@doctor_bp.route("/availability/<int:slot_id>/delete", methods=["POST"])
@role_required("doctor")
def delete_availability(slot_id):
    doctor = current_doctor()
    execute("DELETE FROM doctor_availability WHERE id = %s AND doctor_id = %s", (slot_id, doctor["id"]))
    flash("Availability removed.", "success")
    return redirect(url_for("doctor.availability"))


@doctor_bp.route("/profile", methods=["GET", "POST"])
@role_required("doctor")
def profile():
    doctor = current_doctor()
    if request.method == "POST":
        execute("UPDATE users SET name = %s, phone = %s WHERE id = %s", (request.form.get("name", "").strip(), request.form.get("phone", "").strip(), session["user_id"]))
        execute("UPDATE doctors SET specialization = %s, qualification = %s, experience = %s, consultation_fee = %s, profile_description = %s WHERE id = %s", (request.form.get("specialization", "").strip(), request.form.get("qualification", "").strip(), request.form.get("experience", 0), request.form.get("consultation_fee", 0), request.form.get("profile_description", "").strip(), doctor["id"]))
        session["name"] = request.form.get("name", "").strip()
        flash("Profile updated.", "success")
        return redirect(url_for("doctor.profile"))
    return render_template("doctor/profile.html", doctor=doctor)
