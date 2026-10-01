# CarePoint Hospital Management System

CarePoint is a production-ready Flask-based hospital management platform designed for clinics and small hospitals. It supports patient onboarding, secure OTP-based authentication, appointment scheduling, doctor management, and role-based administrative workflows.

## Overview

This application helps manage:

- Patient registration and verification
- Doctor and admin authentication
- Appointment booking and status tracking
- Doctor availability management
- Hospital administration and reporting
- Secure email-based OTP flows for login and password recovery

## Key Features

- Patient registration with six-digit email OTP verification
- Password reset via secure email-based OTP flow
- Login OTP for patients, doctors, and administrators
- Role-based access control for patients, doctors, and admins
- Doctor profile, department, and availability management
- Appointment booking with conflict validation
- Patient appointment history and cancellation
- Doctor-side acceptance, rejection, and completion of appointments
- Admin dashboard for user and department oversight
- Responsive Bootstrap-powered UI

## Tech Stack

- Python 3.10+
- Flask 3
- MySQL 8+
- mysql-connector-python
- Bootstrap 5
- JavaScript
- SMTP email integration
- Werkzeug password hashing

## System Requirements

Before running the app, make sure you have:

- Python 3.10 or newer
- MySQL Server 8 or newer
- A working SMTP provider such as Gmail with App Password support
- A valid `.env` configuration file

> If you use Gmail, enable two-factor authentication before generating an App Password.

## Quick Start

### 1. Create and activate a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow scripts for the current user, then activate:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

#### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

When activated, your terminal prompt usually shows `(.venv)`. Run the following setup commands in that same activated terminal.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Copy the sample environment file:

```bash
Copy-Item .env.example .env
```

Then update `.env` with your actual values:

```dotenv
SECRET_KEY=your-very-secure-secret-key
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

Do not commit `.env` to version control.

### 4. Create the database schema

Run the SQL schema in MySQL:

```powershell
mysql -u root -p < database\schema.sql
```

You can also import the file in MySQL Workbench manually. The schema creates the `hospital_management` database and the required tables, indexes, constraints, and sample hospital departments.

### 5. Create the first administrator

```powershell
python seed_admin.py
```

Follow the prompts to create the initial admin account. This account is used to create doctors, manage departments, and configure hospital settings.

### 6. Run the application

```powershell
python app.py
```

Then open the app in your browser:

```text
http://127.0.0.1:5000
```

## Authentication and Security Flow

The application uses secure, role-based authentication patterns:

- Passwords are stored with Werkzeug hashing
- OTP values are generated using cryptographically secure random values
- OTP hashes are stored in session data rather than in plaintext
- Expiry and resend throttling are enforced for OTP operations
- Route access is restricted according to user type

### OTP workflow

A patient submits registration details. The server validates the input, generates a six-digit OTP, stores only the hashed value and expiry time in the session, and sends the OTP via email. After verification, the account is activated and the OTP is cleared.

The same pattern is used for:

- Patient login
- Doctor login
- Admin login
- Password reset

## Appointment Workflow

Patients can:

- Browse doctors
- View doctor availability
- Book an appointment for a valid date and time
- View appointment history
- Cancel active bookings

Doctors can:

- Review pending appointments
- Accept or reject requests
- Mark completed visits
- Manage availability

Admins can:

- Activate or deactivate doctors
- Review department records
- Manage appointment flow
- Monitor hospital records and activity

## Project Structure

```text
HMS/
├── app.py
├── config.py
├── db.py
├── seed_admin.py
├── requirements.txt
├── .env.example
├── .gitignore
├── database/
│   └── schema.sql
├── routes/
│   ├── admin.py
│   ├── auth.py
│   ├── doctor.py
│   ├── main.py
│   └── patient.py
├── services/
│   ├── email_service.py
│   └── otp_service.py
├── static/
│   ├── css/
│   └── js/
├── templates/
├── utils/
│   ├── decorators.py
│   └── validators.py
└── README.md
```

## Deployment Notes

For production deployment:

- Use a strong random `SECRET_KEY`
- Run the app behind HTTPS
- Use a dedicated MySQL user with least-privilege permissions
- Keep environment variables in your hosting platform's secret manager
- Disable Flask debug mode
- Use a production WSGI server such as Gunicorn or Waitress

### Gunicorn example

```bash
gunicorn app:app
```

### Waitress example

```powershell
pip install waitress
waitress-serve --listen=127.0.0.1:8000 app:app
```

## Recommended Validation Checklist

Before releasing or testing the app, verify:

1. User registration works with valid email OTP verification
2. Duplicate emails are rejected
3. Invalid OTP values and expired OTPs are handled properly
4. Password resets work for verified accounts
5. Doctor availability is enforced during appointment booking
6. Appointment conflict rules block duplicate bookings
7. Patient, doctor, and admin route permissions work as expected
8. Admin account creation succeeds and the dashboard loads correctly

## License

This project is intended for educational and hospital-management use cases. Review your local licensing and compliance requirements before production deployment.
