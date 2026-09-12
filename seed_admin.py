from getpass import getpass

from werkzeug.security import generate_password_hash

from app import app
from db import execute, fetch_one


with app.app_context():
    email = input("Admin email: ").strip().lower()
    name = input("Admin name: ").strip() or "Hospital Administrator"
    password = getpass("Admin password (8+ characters): ")
    if fetch_one("SELECT id FROM users WHERE email = %s", (email,)):
        print("That email already exists.")
    else:
        execute("INSERT INTO users (name, email, phone, password_hash, role, email_verified) VALUES (%s, %s, %s, %s, 'admin', TRUE)", (name, email, "", generate_password_hash(password)))
        print("Admin account created.")
