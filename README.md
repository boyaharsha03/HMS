# CarePoint Hospital Management System

A deployment-ready Flask and MySQL hospital management system for patient registration, secure email OTP verification, doctor availability, online appointment booking, and role-based hospital administration.

## Features

- Patient registration with six-digit SMTP email OTP, five-minute expiry, hashed session storage, and resend throttling.
- Werkzeug password hashing, Flask sessions, protected routes, and patient/doctor/admin authorization.
- Patient and doctor login OTP on every login, plus email OTP password recovery.
- Doctor directory with search, profiles, departments, availability, and consultation details.
- Appointment booking with backend date, doctor availability, and active-slot conflict validation.
- Patient appointment history and cancellation.
- Doctor appointment acceptance, rejection, completion, patient details, and availability management.
- Admin dashboard statistics, doctor activation, patient directory, department management, appointment status management, and availability overview.
- Responsive Bootstrap 5 interface with no frontend-only placeholder workflows.

## Technology

Python 3.10+, Flask 3, MySQL 8+, Bootstrap 5, JavaScript, SMTP, Werkzeug, and `mysql-connector-python`.

## System Requirements

Install Python 3.10 or newer, MySQL Server 8 or newer, and a Gmail account with an App Password (or another SMTP provider). Gmail accounts must have two-factor authentication enabled before creating an App Password.

## Installation

### Windows PowerShell

```powershell
cd C:\Users\boyah\OneDrive\Desktop\HMS
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### MySQL setup

Start MySQL, then run the schema from a MySQL client:

```powershell
mysql -u root -p < database\schema.sql
```

Or open `database/schema.sql` in MySQL Workbench and execute it. The script creates the `hospital_management` database, tables, foreign keys, indexes, constraints, and sample departments. It does not insert demo users, patients, doctors, appointments, or availability records.

### Environment configuration

Edit `.env` and provide:

```dotenv
SECRET_KEY=use-a-long-random-value
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=your_mysql_password
DATABASE_NAME=hospital_management
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
OTP_EXPIRY_MINUTES=5
OTP_RESEND_SECONDS=60
```

Never commit `.env`. SMTP credentials belong only in environment variables.

### Create the first administrator

After the schema is loaded and `.env` is configured:

```powershell
python seed_admin.py
```

Choose an email and password of at least eight characters. Doctors and patients can then be added through the application. The temporary password entered during doctor creation must be shared securely.

### Run the application

```powershell
python app.py
```

Open http://127.0.0.1:5000 in a browser.

## OTP workflow

A patient submits registration details. Flask validates the fields, generates a cryptographically random six-digit OTP, stores only its SHA-256 digest and expiry in the signed session, and sends the code through SMTP. The verification route checks email binding, expiry, and constant-time digest equality, then removes the OTP before creating the verified patient account. Resend requests are limited by `OTP_RESEND_SECONDS`.

For local development without SMTP, configure a test SMTP provider such as Mailtrap. The application intentionally does not use a fixed development OTP.

Patient and doctor accounts receive a fresh email OTP on every login after the password is accepted. Administrators use direct password login. The Forgot password link sends a separate reset OTP and allows the patient or doctor to set a new password. Admins can remove doctor access by deactivating a doctor; this preserves the doctor's appointment history and can be reversed with Restore access.

## Appointment workflow

A patient logs in, selects a doctor, opens the booking form, selects a future date and time, and submits a reason. The server verifies that the requested day/time matches an active doctor availability record and that no non-cancelled/non-rejected appointment already occupies the slot. The appointment begins as `Pending`. Doctors can accept or reject it, then mark accepted visits as completed. Patients can cancel pending or accepted visits.

## Project structure

```text
HMS/
├── app.py
├── config.py
├── db.py
├── seed_admin.py
├── requirements.txt
├── .env.example
├── database/schema.sql
├── routes/main.py auth.py patient.py doctor.py admin.py
├── services/otp_service.py email_service.py
├── utils/decorators.py validators.py
├── templates/
└── static/css/style.css static/js/script.js
```

## Testing checklist

1. Register with valid details and confirm the OTP email.
2. Try duplicate email, invalid email, mismatched passwords, incorrect OTP, expired OTP, and resend throttling.
3. Log in with valid and invalid passwords; verify unverified users are blocked; log out.
4. Create a doctor and availability slot as admin.
5. Book a matching patient appointment, then try the same active slot again.
6. Cancel as patient; accept, reject, and complete as doctor.
7. Confirm patients cannot open doctor/admin routes and doctors cannot open admin routes.

A configured MySQL server and SMTP provider are required for end-to-end workflow tests. Python compilation and route registration can be checked without either service.

## Deployment

Use a production WSGI server such as Waitress or Gunicorn behind HTTPS, set a strong random `SECRET_KEY`, use a dedicated MySQL user with least-privilege access, store environment variables in the hosting platform's secret manager, disable Flask debug mode, and configure SMTP with an application password. Add CSRF protection and a reverse-proxy rate limiter before exposing write routes to the public internet.

For a Windows demonstration deployment, install Waitress and run:

```powershell
pip install waitress
waitress-serve --listen=127.0.0.1:8000 app:app
```
