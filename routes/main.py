from flask import Blueprint, render_template

from db import fetch_all

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    doctors = fetch_all(
        """SELECT d.id, u.name, d.specialization, d.qualification, d.experience,
                  dep.name AS department
           FROM doctors d JOIN users u ON u.id = d.user_id
           LEFT JOIN departments dep ON dep.id = d.department_id
           WHERE d.status = 'Active' ORDER BY d.experience DESC LIMIT 4"""
    )
    departments = fetch_all("SELECT id, name, description FROM departments ORDER BY name")
    return render_template("index.html", doctors=doctors, departments=departments)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/doctors")
def doctors():
    doctors = fetch_all(
        """SELECT d.id, u.name, d.specialization, d.qualification, d.experience,
                  d.consultation_fee, dep.name AS department
           FROM doctors d JOIN users u ON u.id = d.user_id
           LEFT JOIN departments dep ON dep.id = d.department_id
           WHERE d.status = 'Active' ORDER BY u.name"""
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
    return render_template("doctors.html", doctors=doctors)


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")
