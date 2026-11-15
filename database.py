"""
database.py
Creates the SQLite file and holds every SQL query used by the application.

Keeping all database code in one file means the GUI screens never touch SQL,
which makes the project easier to read and to explain.
"""

import os
import sqlite3
from datetime import datetime

# The database file is stored next to the program.
DB_PATH = os.environ.get(
    "ATTENDTRACK_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance_tracker.db"),
)

# The four statuses allowed by the proposal.
STATUSES = ("Present", "Absent", "Late", "Excused")

DEFAULT_SETTINGS = {
    "school_name": "Samtse College of Education",
    "academic_year": "2025 - 26",
    "late_threshold": "15",
    "min_percentage": "75",
    "track_saturdays": "no",
}


# ---------------- CONNECTION ----------------

def get_connection():
    """Open a connection with foreign keys turned on."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Create all tables the first time the program runs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            phone         TEXT    DEFAULT '',
            department    TEXT    DEFAULT '',
            class_label   TEXT    DEFAULT '',
            created_at    TEXT    NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            student_id TEXT    NOT NULL,
            name       TEXT    NOT NULL,
            class_name TEXT    NOT NULL,
            section    TEXT    NOT NULL,
            created_at TEXT    NOT NULL,
            UNIQUE (owner_id, student_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            student_row INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            date        TEXT    NOT NULL,
            status      TEXT    NOT NULL CHECK (status IN ('Present','Absent','Late','Excused')),
            UNIQUE (student_row, date)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    # Fill the settings table with defaults only when a key is missing.
    for key, value in DEFAULT_SETTINGS.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    conn.commit()
    conn.close()


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------- USERS ----------------

def add_user(name, email, password_hash):
    """Insert a new account and return its id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, now_text()),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def find_user_by_email(email):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def find_user_by_id(user_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_user_profile(user_id, name, email, phone, department, class_label):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE users
               SET name = ?, email = ?, phone = ?, department = ?, class_label = ?
             WHERE id = ?
            """,
            (name, email, phone, department, class_label, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def update_user_password(user_id, password_hash):
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        conn.commit()
    finally:
        conn.close()


def email_taken(email, exclude_user_id=None):
    """True when another account already uses this email address."""
    conn = get_connection()
    try:
        if exclude_user_id is None:
            row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?", (email, exclude_user_id)
            ).fetchone()
        return row is not None
    finally:
        conn.close()


# ---------------- STUDENTS ----------------

def add_student(owner_id, student_id, name, class_name, section):
    """Insert a student and return its row id, or None when the ID is taken."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO students (owner_id, student_id, name, class_name, section, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (owner_id, student_id, name, class_name, section, now_text()),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def student_id_exists(owner_id, student_id, exclude_row=None):
    conn = get_connection()
    try:
        if exclude_row is None:
            row = conn.execute(
                "SELECT id FROM students WHERE owner_id = ? AND student_id = ?",
                (owner_id, student_id),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM students WHERE owner_id = ? AND student_id = ? AND id != ?",
                (owner_id, student_id, exclude_row),
            ).fetchone()
        return row is not None
    finally:
        conn.close()


def update_student(row_id, owner_id, student_id, name, class_name, section):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE students
               SET student_id = ?, name = ?, class_name = ?, section = ?
             WHERE id = ? AND owner_id = ?
            """,
            (student_id, name, class_name, section, row_id, owner_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_student(row_id, owner_id):
    """Delete a student and, through the foreign key, their attendance rows."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM attendance WHERE student_row = ? AND owner_id = ?", (row_id, owner_id))
        conn.execute("DELETE FROM students WHERE id = ? AND owner_id = ?", (row_id, owner_id))
        conn.commit()
    finally:
        conn.close()


def fetch_students(owner_id, search="", class_name="", section=""):
    """Return student rows for one teacher, optionally filtered."""
    sql = "SELECT * FROM students WHERE owner_id = ?"
    params = [owner_id]

    if search:
        sql += " AND (student_id LIKE ? OR name LIKE ?)"
        params += ["%" + search + "%", "%" + search + "%"]
    if class_name:
        sql += " AND class_name = ?"
        params.append(class_name)
    if section:
        sql += " AND section = ?"
        params.append(section)

    sql += " ORDER BY class_name, section, name"

    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def fetch_student_row(owner_id, row_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM students WHERE id = ? AND owner_id = ?", (row_id, owner_id)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def fetch_classes(owner_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT class_name FROM students WHERE owner_id = ? ORDER BY class_name",
            (owner_id,),
        ).fetchall()
        return [r["class_name"] for r in rows]
    finally:
        conn.close()


def fetch_sections(owner_id, class_name=""):
    sql = "SELECT DISTINCT section FROM students WHERE owner_id = ?"
    params = [owner_id]
    if class_name:
        sql += " AND class_name = ?"
        params.append(class_name)
    sql += " ORDER BY section"

    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [r["section"] for r in rows]
    finally:
        conn.close()


# ---------------- ATTENDANCE ----------------

def save_attendance(owner_id, entries):
    """
    Save a list of (student_row, date, status) tuples.

    INSERT OR REPLACE means a student can be marked again for the same date
    and the old record is updated instead of duplicated.
    """
    if not entries:
        return 0
    conn = get_connection()
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO attendance (owner_id, student_row, date, status)
            VALUES (?, ?, ?, ?)
            """,
            [(int(owner_id), int(student_row), str(date), str(status))
             for student_row, date, status in entries],
        )
        conn.commit()
        return len(entries)
    finally:
        conn.close()


def fetch_attendance_for_date(owner_id, date, class_name="", section=""):
    """Return {student_row: status} already saved for one date."""
    sql = "SELECT student_row, status FROM attendance WHERE owner_id = ? AND date = ?"
    params = [owner_id, date]
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return {r["student_row"]: r["status"] for r in rows}
    finally:
        conn.close()


def count_attendance_on(owner_id, date, status):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) AS n FROM attendance WHERE owner_id = ? AND date = ? AND status = ?",
            (owner_id, date, status),
        ).fetchone()["n"]
    finally:
        conn.close()


def fetch_all_dates(owner_id):
    """Every date that has attendance, oldest first (used to set report ranges)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT date FROM attendance WHERE owner_id = ? ORDER BY date", (owner_id,)
        ).fetchall()
        return [r["date"] for r in rows]
    finally:
        conn.close()


# ---------------- SETTINGS ----------------

def load_settings():
    """Return all settings as a dictionary, with defaults filled in."""
    values = dict(DEFAULT_SETTINGS)
    conn = get_connection()
    try:
        for row in conn.execute("SELECT key, value FROM settings").fetchall():
            values[row["key"]] = row["value"]
    finally:
        conn.close()
    return values


def save_settings(values):
    conn = get_connection()
    try:
        for key, value in values.items():
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
        conn.commit()
    finally:
        conn.close()


# ---------------- DEMO DATA SUPPORT ----------------

def clear_demo_data(owner_id, demo_class):
    """Remove only the records that were tagged as demonstration data."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id FROM students WHERE owner_id = ? AND class_name = ?",
            (owner_id, demo_class),
        ).fetchall()
        for row in rows:
            conn.execute("DELETE FROM attendance WHERE student_row = ?", (row["id"],))
            conn.execute("DELETE FROM students WHERE id = ?", (row["id"],))
        conn.commit()
        return len(rows)
    finally:
        conn.close()
