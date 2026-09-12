from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from db import execute, fetch_all, fetch_one
from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    stats = fetch_one("""SELECT (SELECT COUNT(*) FROM users WHERE role = 'patient') patients, (SELECT COUNT(*) FROM doctors) doctors, (SELECT COUNT(*) FROM departments) departments, (SELECT COUNT(*) FROM appointments) appointments, (SELECT COUNT(*) FROM appointments WHERE status = 'Pending') pending, (SELECT COUNT(*) FROM appointments WHERE status = 'Completed') completed""")
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/doctors", methods=["GET", "POST"])
@role_required("admin")
def doctors():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        availability_day = request.form.get("availability_day", "").strip()
        availability_start = request.form.get("availability_start", "").strip()
        availability_end = request.form.get("availability_end", "").strip()
        if fetch_one("SELECT id FROM users WHERE email = %s", (email,)):
            flash("That email is already registered.", "danger")
        elif bool(availability_day) != bool(availability_start) or bool(availability_day) != bool(availability_end):
            flash("Fill in all availability fields or leave all three empty.", "danger")
        elif availability_start and availability_end and availability_start >= availability_end:
            flash("Availability end time must be later than start time.", "danger")
        else:
            user_id = execute("INSERT INTO users (name, email, phone, password_hash, role, email_verified) VALUES (%s, %s, %s, %s, 'doctor', TRUE)", (name, email, request.form.get("phone", "").strip(), generate_password_hash(request.form.get("password", "Doctor@123"))))
            doctor_id = execute("INSERT INTO doctors (user_id, department_id, specialization, qualification, experience, consultation_fee, profile_description) VALUES (%s, NULLIF(%s, ''), %s, %s, %s, %s, %s)", (user_id, request.form.get("department_id", ""), request.form.get("specialization", ""), request.form.get("qualification", ""), request.form.get("experience", 0), request.form.get("consultation_fee", 0), request.form.get("profile_description", "")))
            if availability_day:
                execute("INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time) VALUES (%s, %s, %s, %s)", (doctor_id, availability_day, availability_start, availability_end))
            flash("Doctor added. Share the temporary password securely.", "success")
    doctors = fetch_all("SELECT d.*, u.name, u.email, u.phone, dep.name department FROM doctors d JOIN users u ON u.id = d.user_id LEFT JOIN departments dep ON dep.id = d.department_id ORDER BY u.name")
    departments = fetch_all("SELECT * FROM departments ORDER BY name")
    return render_template("admin/doctors.html", doctors=doctors, departments=departments)


@admin_bp.route("/doctors/<int:doctor_id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_doctor(doctor_id):
    execute("UPDATE doctors SET status = IF(status = 'Active', 'Inactive', 'Active') WHERE id = %s", (doctor_id,))
    flash("Doctor status updated.", "success")
    return redirect(url_for("admin.doctors"))


@admin_bp.route("/doctors/<int:doctor_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_doctor(doctor_id):
    doctor = fetch_one(
        """SELECT d.*, u.name, u.email, u.phone
           FROM doctors d JOIN users u ON u.id = d.user_id
           WHERE d.id = %s""",
        (doctor_id,),
    )
    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for("admin.doctors"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        availability_days = request.form.getlist("availability_days")
        availability_start = request.form.get("availability_start", "").strip()
        availability_end = request.form.get("availability_end", "").strip()
        apply_everyday = request.form.get("apply_everyday") == "1"
        duplicate = fetch_one("SELECT id FROM users WHERE email = %s AND id <> %s", (email, doctor["user_id"]))
        if duplicate:
            flash("That email is already registered.", "danger")
        elif not apply_everyday and availability_days and (not availability_start or not availability_end):
            flash("Enter both start and end times for the selected days.", "danger")
        elif not apply_everyday and not availability_days and (availability_start or availability_end):
            flash("Select at least one day for these hours, or select every day.", "danger")
        elif apply_everyday and (not availability_start or not availability_end):
            flash("Enter both start and end times for the everyday schedule.", "danger")
        elif availability_start and availability_end and availability_start >= availability_end:
            flash("Availability end time must be later than start time.", "danger")
        else:
            execute("UPDATE users SET name = %s, email = %s, phone = %s, status = %s WHERE id = %s", (request.form.get("name", "").strip(), email, request.form.get("phone", "").strip(), request.form.get("user_status", "Active"), doctor["user_id"]))
            execute("UPDATE doctors SET department_id = NULLIF(%s, ''), specialization = %s, qualification = %s, experience = %s, consultation_fee = %s, profile_description = %s, status = %s WHERE id = %s", (request.form.get("department_id", ""), request.form.get("specialization", "").strip(), request.form.get("qualification", "").strip(), request.form.get("experience", 0), request.form.get("consultation_fee", 0), request.form.get("profile_description", "").strip(), request.form.get("doctor_status", "Active"), doctor_id))
            if apply_everyday or availability_days:
                execute("DELETE FROM doctor_availability WHERE doctor_id = %s AND status = 'Active'", (doctor_id,))
                days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday") if apply_everyday else availability_days
                for day in days:
                    execute("INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time) VALUES (%s, %s, %s, %s)", (doctor_id, day, availability_start, availability_end))
            flash("Doctor details updated.", "success")
            return redirect(url_for("admin.doctors"))
    departments = fetch_all("SELECT * FROM departments ORDER BY name")
    availability = fetch_all("SELECT id, day_of_week, start_time, end_time FROM doctor_availability WHERE doctor_id = %s AND status = 'Active' ORDER BY id", (doctor_id,))
    return render_template("admin/edit_doctor.html", doctor=doctor, departments=departments, availability=availability)


@admin_bp.route("/patients")
@role_required("admin")
def patients():
    rows = fetch_all("SELECT p.id patient_id, u.id user_id, u.name, u.email, u.phone, u.created_at, u.status, p.date_of_birth, p.gender, p.address FROM users u JOIN patients p ON p.user_id = u.id ORDER BY u.created_at DESC")
    return render_template("admin/patients.html", patients=rows)


@admin_bp.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_patient(patient_id):
    patient = fetch_one(
        """SELECT p.id patient_id, p.user_id, u.name, u.email, u.phone, u.status,
                  p.date_of_birth, p.gender, p.address
           FROM patients p JOIN users u ON u.id = p.user_id
           WHERE p.id = %s""",
        (patient_id,),
    )
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("admin.patients"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        duplicate = fetch_one("SELECT id FROM users WHERE email = %s AND id <> %s", (email, patient["user_id"]))
        if duplicate:
            flash("That email is already registered.", "danger")
        else:
            execute("UPDATE users SET name = %s, email = %s, phone = %s, status = %s WHERE id = %s", (request.form.get("name", "").strip(), email, request.form.get("phone", "").strip(), request.form.get("user_status", "Active"), patient["user_id"]))
            execute("UPDATE patients SET date_of_birth = NULLIF(%s, ''), gender = %s, address = %s WHERE id = %s", (request.form.get("date_of_birth", ""), request.form.get("gender", "").strip(), request.form.get("address", "").strip(), patient_id))
            flash("Patient details updated.", "success")
            return redirect(url_for("admin.patients"))
    return render_template("admin/edit_patient.html", patient=patient)


@admin_bp.route("/departments", methods=["GET", "POST"])
@role_required("admin")
def departments():
    if request.method == "POST":
        execute("INSERT INTO departments (name, description) VALUES (%s, %s)", (request.form.get("name", "").strip(), request.form.get("description", "").strip()))
        flash("Department added.", "success")
    return render_template("admin/departments.html", departments=fetch_all("SELECT * FROM departments ORDER BY name"))


@admin_bp.route("/departments/<int:department_id>/delete", methods=["POST"])
@role_required("admin")
def delete_department(department_id):
    execute("DELETE FROM departments WHERE id = %s", (department_id,))
    flash("Department removed.", "success")
    return redirect(url_for("admin.departments"))


@admin_bp.route("/appointments")
@role_required("admin")
def appointments():
    rows = fetch_all("""SELECT a.*, pu.name patient_name, du.name doctor_name, dep.name department FROM appointments a JOIN patients p ON p.id = a.patient_id JOIN users pu ON pu.id = p.user_id JOIN doctors d ON d.id = a.doctor_id JOIN users du ON du.id = d.user_id LEFT JOIN departments dep ON dep.id = d.department_id ORDER BY a.appointment_date DESC, a.appointment_time DESC""")
    return render_template("admin/appointments.html", appointments=rows)


@admin_bp.route("/appointments/<int:appointment_id>/status", methods=["POST"])
@role_required("admin")
def appointment_status(appointment_id):
    status = request.form.get("status")
    if status in {"Pending", "Accepted", "Rejected", "Completed", "Cancelled"}:
        execute("UPDATE appointments SET status = %s WHERE id = %s", (status, appointment_id))
        flash("Appointment status updated.", "success")
    return redirect(url_for("admin.appointments"))


@admin_bp.route("/availability")
@role_required("admin")
def availability():
    slots = fetch_all("""SELECT av.*, u.name doctor_name FROM doctor_availability av JOIN doctors d ON d.id = av.doctor_id JOIN users u ON u.id = d.user_id ORDER BY u.name, av.day_of_week""")
    return render_template("admin/availability.html", availability=slots)
