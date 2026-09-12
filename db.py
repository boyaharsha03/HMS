import os
import sqlite3
from datetime import date, datetime
from contextlib import contextmanager
import mysql.connector
from flask import current_app

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "hospital_management.db")

def sqlite_dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def _init_sqlite_db(conn):
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'patient',
        email_verified BOOLEAN NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Active',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    );""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        date_of_birth DATE NULL,
        gender TEXT,
        address TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        department_id INTEGER NULL,
        specialization TEXT NOT NULL,
        qualification TEXT,
        experience INTEGER NOT NULL DEFAULT 0,
        consultation_fee REAL NOT NULL DEFAULT 0,
        available_days TEXT,
        profile_description TEXT,
        status TEXT NOT NULL DEFAULT 'Active',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
    );""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS doctor_availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        day_of_week TEXT NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active',
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
    );""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date DATE NOT NULL,
        appointment_time TIME NOT NULL,
        reason TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
    );""")

    c.execute("SELECT COUNT(*) AS cnt FROM departments")
    if c.fetchone()["cnt"] == 0:
        c.executemany("INSERT INTO departments (name, description) VALUES (?, ?)", [
            ('Cardiology', 'Heart and cardiovascular care'),
            ('Neurology', 'Brain and nervous system care'),
            ('Pediatrics', 'Medical care for children'),
            ('Orthopedics', 'Bones, joints, and movement care'),
            ('General Medicine', 'Primary and preventive care')
        ])

    conn.commit()
    c.close()

def _get_sqlite_conn():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite_dict_factory
    def dayname(val):
        if not val:
            return None
        try:
            return datetime.strptime(str(val)[:10], '%Y-%m-%d').strftime('%A')
        except Exception:
            return None

    conn.create_function('DAYNAME', 1, dayname)
    conn.create_function('CURDATE', 0, lambda: date.today().isoformat())
    conn.create_function('IF', 3, lambda cond, a, b: a if cond else b)
    _init_sqlite_db(conn)
    return conn

@contextmanager
def get_db():
    db_config = current_app.config.get("DATABASE_CONFIG", {})
    db_type = os.getenv("DATABASE_TYPE", "auto")
    
    if db_type == "sqlite":
        conn = _get_sqlite_conn()
        try:
            yield conn, "sqlite"
        finally:
            conn.close()
        return

    try:
        connection = mysql.connector.connect(**db_config)
        try:
            yield connection, "mysql"
        finally:
            connection.close()
    except Exception as err:
        current_app.logger.warning(f"MySQL connection failed ({err}). Using SQLite database fallback.")
        conn = _get_sqlite_conn()
        try:
            yield conn, "sqlite"
        finally:
            conn.close()

@contextmanager
def cursor(dictionary=True):
    with get_db() as (connection, db_type):
        if db_type == "mysql":
            db_cursor = connection.cursor(dictionary=dictionary)
            try:
                yield connection, db_cursor, "mysql"
            finally:
                db_cursor.close()
        else:
            db_cursor = connection.cursor()
            try:
                yield connection, db_cursor, "sqlite"
            finally:
                db_cursor.close()

def fetch_one(query, params=()):
    with cursor() as (_, db_cursor, db_type):
        if db_type == "sqlite":
            query = query.replace("%s", "?")
        db_cursor.execute(query, params)
        return db_cursor.fetchone()

def fetch_all(query, params=()):
    with cursor() as (_, db_cursor, db_type):
        if db_type == "sqlite":
            query = query.replace("%s", "?")
        db_cursor.execute(query, params)
        return db_cursor.fetchall()

def execute(query, params=(), commit=True):
    with cursor() as (connection, db_cursor, db_type):
        if db_type == "sqlite":
            query = query.replace("%s", "?")
        db_cursor.execute(query, params)
        if commit:
            connection.commit()
        return db_cursor.lastrowid

