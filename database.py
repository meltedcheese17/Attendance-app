"""
database.py — SQLite persistence layer for the Attendance Tracker.
All schema creation, queries, inserts, and updates live here.
"""

import sqlite3
import os
from datetime import date, time, datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─── Schema ──────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    role       TEXT    NOT NULL,
    active     INTEGER NOT NULL DEFAULT 1,
    created_at TEXT    NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS schedules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id     INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    work_days       TEXT    NOT NULL DEFAULT 'Mon,Tue,Wed,Thu,Fri',
    expected_in     TEXT    NOT NULL DEFAULT '09:00',
    expected_out    TEXT    NOT NULL DEFAULT '18:00',
    UNIQUE(employee_id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id    INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    log_date       TEXT    NOT NULL,
    present        INTEGER NOT NULL DEFAULT 0,
    arrival_time   TEXT,
    departure_time TEXT,
    status         TEXT    NOT NULL DEFAULT 'Absent',
    notes          TEXT,
    UNIQUE(employee_id, log_date)
);
"""

PRESET_ROLES = ["Founder", "Director", "Manager", "Employee", "Intern"]
DAYS_OF_WEEK  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # seed default company name if absent
        conn.execute(
            "INSERT OR IGNORE INTO settings VALUES ('company_name', 'My Company')"
        )
        conn.commit()


# ─── Settings ─────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()


# ─── Employees ────────────────────────────────────────────────────────────────

def add_employee(name: str, role: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO employees(name, role) VALUES(?,?)", (name.strip(), role.strip())
        )
        emp_id = cur.lastrowid
        # create a default schedule
        conn.execute(
            "INSERT OR IGNORE INTO schedules(employee_id) VALUES(?)", (emp_id,)
        )
        conn.commit()
    return emp_id


def get_all_employees(active_only: bool = True):
    with get_conn() as conn:
        if active_only:
            rows = conn.execute(
                "SELECT * FROM employees WHERE active=1 ORDER BY name"
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM employees ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def get_employee(emp_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM employees WHERE id=?", (emp_id,)).fetchone()
    return dict(row) if row else None


def update_employee(emp_id: int, name: str, role: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE employees SET name=?, role=? WHERE id=?",
            (name.strip(), role.strip(), emp_id),
        )
        conn.commit()


def deactivate_employee(emp_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE employees SET active=0 WHERE id=?", (emp_id,))
        conn.commit()


def delete_employee(emp_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM employees WHERE id=?", (emp_id,))
        conn.commit()


# ─── Schedules ────────────────────────────────────────────────────────────────

def get_schedule(emp_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM schedules WHERE employee_id=?", (emp_id,)
        ).fetchone()
    return dict(row) if row else None


def upsert_schedule(emp_id: int, work_days: list[str], expected_in: str, expected_out: str):
    days_str = ",".join(work_days)
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO schedules(employee_id, work_days, expected_in, expected_out)
               VALUES(?,?,?,?)
               ON CONFLICT(employee_id) DO UPDATE SET
                 work_days=excluded.work_days,
                 expected_in=excluded.expected_in,
                 expected_out=excluded.expected_out""",
            (emp_id, days_str, expected_in, expected_out),
        )
        conn.commit()


# ─── Attendance ───────────────────────────────────────────────────────────────

def _calc_status(
    present: bool,
    arrival: Optional[str],
    departure: Optional[str],
    expected_in: str,
    expected_out: str,
) -> str:
    """Derive Full Day / Half Day / Absent based on hours worked vs scheduled."""
    if not present:
        return "Absent"
    if not arrival or not departure:
        return "Present"

    def to_minutes(t: str) -> int:
        try:
            h, m = map(int, t.split(":"))
            return h * 60 + m
        except Exception:
            return 0

    scheduled_minutes = to_minutes(expected_out) - to_minutes(expected_in)
    actual_minutes    = to_minutes(departure) - to_minutes(arrival)

    if scheduled_minutes <= 0:
        return "Present"

    ratio = actual_minutes / scheduled_minutes
    if ratio >= 0.85:
        return "Full Day"
    elif ratio >= 0.45:
        return "Half Day"
    else:
        return "Short Day"


def upsert_attendance(
    emp_id: int,
    log_date: str,
    present: bool,
    arrival: Optional[str],
    departure: Optional[str],
    notes: str = "",
):
    schedule = get_schedule(emp_id)
    exp_in  = schedule["expected_in"]  if schedule else "09:00"
    exp_out = schedule["expected_out"] if schedule else "18:00"
    status  = _calc_status(present, arrival, departure, exp_in, exp_out)

    with get_conn() as conn:
        conn.execute(
            """INSERT INTO attendance
                 (employee_id, log_date, present, arrival_time, departure_time, status, notes)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(employee_id, log_date) DO UPDATE SET
                 present=excluded.present,
                 arrival_time=excluded.arrival_time,
                 departure_time=excluded.departure_time,
                 status=excluded.status,
                 notes=excluded.notes""",
            (emp_id, log_date, int(present), arrival or None, departure or None, status, notes),
        )
        conn.commit()
    return status


def get_attendance_for_date(log_date: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT a.*, e.name, e.role
               FROM attendance a
               JOIN employees e ON e.id = a.employee_id
               WHERE a.log_date = ? AND e.active = 1
               ORDER BY e.name""",
            (log_date,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_attendance_range(emp_id: int, start: str, end: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM attendance
               WHERE employee_id=? AND log_date BETWEEN ? AND ?
               ORDER BY log_date""",
            (emp_id, start, end),
        ).fetchall()
    return [dict(r) for r in rows]


def get_monthly_summary(year: int, month: int) -> list[dict]:
    """Returns per-employee aggregated stats for the given month."""
    start = f"{year:04d}-{month:02d}-01"
    end   = f"{year:04d}-{month:02d}-31"
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT
                 e.id,
                 e.name,
                 e.role,
                 COUNT(CASE WHEN a.status='Full Day'  THEN 1 END) AS full_days,
                 COUNT(CASE WHEN a.status='Half Day'  THEN 1 END) AS half_days,
                 COUNT(CASE WHEN a.status='Short Day' THEN 1 END) AS short_days,
                 COUNT(CASE WHEN a.status='Present'   THEN 1 END) AS present_unmarked,
                 COUNT(CASE WHEN a.present=1          THEN 1 END) AS total_present,
                 COUNT(CASE WHEN a.present=0          THEN 1 END) AS total_absent,
                 COUNT(*) AS total_logged
               FROM employees e
               LEFT JOIN attendance a
                 ON a.employee_id = e.id
                 AND a.log_date BETWEEN ? AND ?
               WHERE e.active = 1
               GROUP BY e.id
               ORDER BY e.name""",
            (start, end),
        ).fetchall()
    return [dict(r) for r in rows]


def get_employee_daily_log(emp_id: int, year: int, month: int) -> list[dict]:
    start = f"{year:04d}-{month:02d}-01"
    end   = f"{year:04d}-{month:02d}-31"
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM attendance
               WHERE employee_id=? AND log_date BETWEEN ? AND ?
               ORDER BY log_date""",
            (emp_id, start, end),
        ).fetchall()
    return [dict(r) for r in rows]
