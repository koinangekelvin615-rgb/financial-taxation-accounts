import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "app_data.db").strip() or "app_data.db"


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _connect() -> sqlite3.Connection:
    parent = os.path.dirname(DB_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(admin_seed: dict | None = None, student_seed: dict | None = None) -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT DEFAULT '',
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                subscription_status TEXT NOT NULL DEFAULT 'Active',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT NOT NULL,
                user_email TEXT NOT NULL,
                phone TEXT NOT NULL,
                plan TEXT NOT NULL,
                amount TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Submitted',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS custom_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                points_json TEXT NOT NULL,
                formula_or_rule TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS custom_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                question TEXT NOT NULL,
                options_json TEXT NOT NULL,
                answer TEXT NOT NULL,
                explanation TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS progress_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                mode TEXT NOT NULL,
                detail TEXT NOT NULL,
                correct_count INTEGER NOT NULL DEFAULT 0,
                total_count INTEGER NOT NULL DEFAULT 0,
                points_earned INTEGER NOT NULL DEFAULT 0,
                max_points INTEGER NOT NULL DEFAULT 0,
                score_label TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('announcement', ?)
            """,
            ("30-Day Full Access is KES 500 via M-Pesa (0700566525).",),
        )

        for seed, role in ((admin_seed, "admin"), (student_seed, "student")):
            if seed and seed.get("email") and seed.get("password_hash"):
                email = seed["email"].strip().lower()
                existing = conn.execute(
                    "SELECT id FROM users WHERE email = ?", (email,)
                ).fetchone()
                if not existing:
                    conn.execute(
                        """
                        INSERT INTO users (email, name, phone, password_hash, role, subscription_status, created_at)
                        VALUES (?, ?, ?, ?, ?, 'Active', ?)
                        """,
                        (
                            email,
                            seed.get("name", role.title()),
                            seed.get("phone", ""),
                            seed["password_hash"],
                            role,
                            _now_str(),
                        ),
                    )
        conn.commit()


def get_user_by_email(email: str) -> dict | None:
    if not email:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(email) = LOWER(?)",
            (email.strip(),),
        ).fetchone()
        return dict(row) if row else None


def create_student_user(email: str, name: str, phone: str, password_hash: str) -> tuple[bool, str]:
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        return False, "Please+enter+a+valid+email+address"
    if get_user_by_email(clean_email):
        return False, "An+account+with+that+email+already+exists"

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO users (email, name, phone, password_hash, role, subscription_status, created_at)
            VALUES (?, ?, ?, ?, 'student', 'Pending', ?)
            """,
            (clean_email, name.strip(), phone.strip(), password_hash, _now_str()),
        )
        conn.commit()
    return True, "Account+created.+You+can+sign+in+now."


def list_all_users() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, email, name, phone, role, subscription_status, created_at FROM users ORDER BY id ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def set_user_subscription(email: str, status: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET subscription_status = ? WHERE LOWER(email) = LOWER(?)",
            (status, email.strip()),
        )
        conn.commit()


def add_payment(reference: str, user_email: str, phone: str, plan: str, amount: str) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO payments (reference, user_email, phone, plan, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'Submitted', ?)
            """,
            (reference.strip(), user_email.strip().lower(), phone.strip(), plan.strip(), amount.strip(), _now_str()),
        )
        conn.commit()


def list_payments() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM payments ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def update_payment_status(payment_id: int, status: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE payments SET status = ? WHERE id = ?",
            (status, payment_id),
        )
        if status == "Confirmed":
            row = conn.execute(
                "SELECT user_email FROM payments WHERE id = ?", (payment_id,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE users SET subscription_status = 'Active' WHERE LOWER(email) = LOWER(?)",
                    (row["user_email"],),
                )
        conn.commit()


def get_announcement() -> str:
    with _connect() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'announcement'"
        ).fetchone()
        return row["value"] if row else ""


def set_announcement(text: str) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value) VALUES ('announcement', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (text.strip(),),
        )
        conn.commit()


def add_custom_note(
    topic: str,
    category: str,
    summary: str,
    points: list[str],
    formula_or_rule: str = "",
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO custom_notes (topic, category, summary, points_json, formula_or_rule, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                topic.strip(),
                category.strip(),
                summary.strip(),
                json.dumps(points),
                formula_or_rule.strip(),
                _now_str(),
            ),
        )
        conn.commit()


def get_custom_notes() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM custom_notes ORDER BY id ASC").fetchall()
        notes = []
        for r in rows:
            try:
                pts = json.loads(r["points_json"])
            except Exception:
                pts = []
            notes.append(
                {
                    "topic": r["topic"],
                    "category": r["category"],
                    "summary": r["summary"],
                    "points": pts,
                    "formula_or_rule": r["formula_or_rule"],
                }
            )
        return notes


def add_custom_question(
    topic: str,
    question: str,
    options: list[str],
    answer: str,
    explanation: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO custom_questions (topic, question, options_json, answer, explanation, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                topic.strip(),
                question.strip(),
                json.dumps(options),
                answer.strip().upper(),
                explanation.strip(),
                _now_str(),
            ),
        )
        conn.commit()


def get_custom_questions(start_id: int = 1) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM custom_questions ORDER BY id ASC").fetchall()
        questions = []
        for offset, r in enumerate(rows):
            try:
                opts = json.loads(r["options_json"])
            except Exception:
                opts = []
            questions.append(
                {
                    "id": start_id + offset,
                    "topic": r["topic"],
                    "question": r["question"],
                    "options": opts,
                    "answer": r["answer"],
                    "explanation": r["explanation"],
                }
            )
        return questions


def log_progress(
    user_email: str,
    mode: str,
    detail: str,
    correct_count: int,
    total_count: int,
    points_earned: int,
    max_points: int,
    score_label: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO progress_logs (
                user_email, mode, detail, correct_count, total_count,
                points_earned, max_points, score_label, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_email.strip().lower(),
                mode,
                detail,
                correct_count,
                total_count,
                points_earned,
                max_points,
                score_label,
                _now_str(),
            ),
        )
        conn.commit()


def get_user_progress_summary(user_email: str) -> dict:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM progress_logs WHERE LOWER(user_email) = LOWER(?) ORDER BY id DESC",
            (user_email.strip(),),
        ).fetchall()

    practice_runs = 0
    practice_correct = 0
    practice_total = 0

    challenge_runs = 0
    challenge_points = 0
    challenge_max_points = 0

    history = []
    for r in rows:
        history.append(
            {
                "date": r["created_at"],
                "mode": r["mode"],
                "detail": r["detail"],
                "score": r["score_label"],
            }
        )
        if r["mode"] == "Topic Practice":
            practice_runs += 1
            practice_correct += r["correct_count"]
            practice_total += r["total_count"]
        elif r["mode"] == "50-Q Challenge":
            challenge_runs += 1
            challenge_points += r["points_earned"]
            challenge_max_points += r["max_points"]

    last_activity = history[0]["date"] if history else "No sessions yet"

    return {
        "practice_runs": practice_runs,
        "practice_correct": practice_correct,
        "practice_total": practice_total,
        "challenge_runs": challenge_runs,
        "challenge_points": challenge_points,
        "challenge_max_points": challenge_max_points,
        "last_activity": last_activity,
        "history": history[:15],
    }