import sqlite3
from datetime import datetime, timedelta

DB_PATH = "taxclass.db"
DATE_FMT = "%Y-%m-%d %H:%M"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_payments_db() -> None:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_email TEXT NOT NULL,
                mpesa_code TEXT NOT NULL UNIQUE,
                amount INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                submitted_at TEXT NOT NULL,
                approved_at TEXT
            )
            """
        )
        cols = [row["name"] for row in cursor.execute("PRAGMA table_info(students)").fetchall()]
        if "is_paid" not in cols:
            cursor.execute("ALTER TABLE students ADD COLUMN is_paid INTEGER NOT NULL DEFAULT 0")
        if "plan_expires_at" not in cols:
            cursor.execute("ALTER TABLE students ADD COLUMN plan_expires_at TEXT")
        conn.commit()
    finally:
        conn.close()


def has_active_plan(student_email: str) -> bool:
    if not student_email:
        return False
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT is_paid, plan_expires_at FROM students WHERE email = ?",
            (student_email.strip().lower(),),
        ).fetchone()
        if not row or row["is_paid"] != 1 or not row["plan_expires_at"]:
            return False
        expires = datetime.strptime(row["plan_expires_at"], DATE_FMT)
        return datetime.now() < expires
    finally:
        conn.close()


def get_plan_expiry(student_email: str) -> str | None:
    if not student_email:
        return None
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT is_paid, plan_expires_at FROM students WHERE email = ?",
            (student_email.strip().lower(),),
        ).fetchone()
        if not row or row["is_paid"] != 1:
            return None
        return row["plan_expires_at"]
    finally:
        conn.close()


def submit_payment(student_email: str, mpesa_code: str, amount: int) -> tuple[bool, str]:
    clean_email = (student_email or "").strip().lower()
    clean_code = (mpesa_code or "").strip().upper()
    if not clean_email or not clean_code:
        return False, "Please enter a valid M-Pesa transaction code."

    conn = _get_connection()
    try:
        existing = conn.execute(
            "SELECT id, status FROM payments WHERE mpesa_code = ?",
            (clean_code,),
        ).fetchone()
        if existing:
            return False, "That M-Pesa code has already been submitted."

        conn.execute(
            """
            INSERT INTO payments (student_email, mpesa_code, amount, status, submitted_at)
            VALUES (?, ?, ?, 'pending', ?)
            """,
            (clean_email, clean_code, int(amount), datetime.now().strftime(DATE_FMT)),
        )
        conn.commit()
        return True, "Payment code submitted. Awaiting verification."
    finally:
        conn.close()


def list_payments(status: str | None = None) -> list[dict]:
    conn = _get_connection()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM payments WHERE status = ? ORDER BY id DESC",
                (status.strip().lower(),),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM payments ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def approve_payment(payment_id: int, days: int = 30) -> bool:
    conn = _get_connection()
    try:
        payment = conn.execute(
            "SELECT student_email, status FROM payments WHERE id = ?",
            (int(payment_id),),
        ).fetchone()
        if not payment:
            return False

        now_str = datetime.now().strftime(DATE_FMT)
        expiry_str = (datetime.now() + timedelta(days=int(days))).strftime(DATE_FMT)

        if payment["status"] != "approved":
            conn.execute(
                "UPDATE payments SET status = 'approved', approved_at = ? WHERE id = ?",
                (now_str, int(payment_id)),
            )

        conn.execute(
            "UPDATE students SET is_paid = 1, plan_expires_at = ? WHERE email = ?",
            (expiry_str, payment["student_email"]),
        )
        conn.commit()
        return True
    finally:
        conn.close()