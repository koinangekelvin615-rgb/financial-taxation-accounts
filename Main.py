from contextlib import asynccontextmanager
import hashlib
import html
import os
import sqlite3
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from payments import (
    approve_payment,
    get_plan_expiry,
    has_active_plan,
    init_payments_db,
    list_payments,
    submit_payment,
)
from quiz import (
    TOPIC_LABELS,
    get_questions,
    get_student_attempts,
    init_quiz_db,
    save_attempt,
)
from tax_notes import get_notes

DB_PATH = "taxclass.db"
SECRET_KEY = os.getenv("TAXCLASS_SECRET_KEY", "dev-only-change-in-production-secret")
ADMIN_EMAIL = os.getenv("TAXCLASS_ADMIN_EMAIL", "admin@taxclasskenya.local").strip().lower()
MPESA_NUMBER_LOCAL = os.getenv("TAXCLASS_MPESA_NUMBER", "0700566525").strip()
MPESA_NUMBER_INTL = (
    "254" + MPESA_NUMBER_LOCAL[1:]
    if MPESA_NUMBER_LOCAL.startswith("0")
    else MPESA_NUMBER_LOCAL
)
PLAN_PRICE_KES = int(os.getenv("TAXCLASS_PLAN_PRICE_KES", "500"))
PLAN_DAYS = int(os.getenv("TAXCLASS_PLAN_DAYS", "30"))
EXAM_DURATION_SECONDS = 15 * 60
EXAM_MAX_QUESTIONS = 10


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_students_db() -> None:
    conn = _get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_paid INTEGER NOT NULL DEFAULT 0,
                plan_expires_at TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_students_db()
    init_quiz_db()
    init_payments_db()
    yield


app = FastAPI(title="TaxClass Kenya", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="taxclass_session",
    same_site="lax",
    https_only=os.getenv("TAXCLASS_HTTPS_ONLY", "false").lower() == "true",
)


def _page(title: str, user_email: str | None, body_html: str) -> HTMLResponse:
    safe_user = html.escape(user_email) if user_email else ""
    nav_right = (
        f'<span class="user-pill">{safe_user}</span> <a href="/logout">Logout</a>'
        if user_email
        else '<a href="/login">Login</a> <a href="/signup">Sign Up</a>'
    )
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>{html.escape(title)} — TaxClass Kenya</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; background: #f4f7f5; color: #1b241e; }}
                header {{ background: #14532d; color: #fff; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }}
                header a {{ color: #dcfce7; text-decoration: none; margin-right: 14px; font-weight: 600; }}
                header a:hover {{ text-decoration: underline; }}
                .user-pill {{ background: #166534; padding: 4px 10px; border-radius: 12px; font-size: 0.9rem; margin-right: 8px; }}
                main {{ max-width: 900px; margin: 28px auto; background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
                .btn {{ display: inline-block; background: #15803d; color: #fff; padding: 9px 15px; border: 0; border-radius: 5px; text-decoration: none; cursor: pointer; font-size: 0.95rem; }}
                .btn:hover {{ background: #166534; }}
                .card {{ border: 1px solid #d1fae5; background: #f0fdf4; padding: 16px; border-radius: 6px; margin-bottom: 16px; }}
                .notice {{ background: #fef9c3; border: 1px solid #fde047; padding: 10px 14px; border-radius: 5px; margin-bottom: 16px; }}
                input, select {{ padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 5px; margin: 4px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
                th, td {{ border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; }}
                th {{ background: #f8fafc; }}
            </style>
        </head>
        <body>
            <header>
                <div>
                    <a href="/">TaxClass Kenya</a>
                    <a href="/dashboard">Dashboard</a>
                    <a href="/notes">Notes</a>
                    <a href="/quiz">Practice Quiz</a>
                    <a href="/exam">Timed Exam</a>
                    <a href="/upgrade">Upgrade</a>
                </div>
                <div>{nav_right}</div>
            </header>
            <main>{body_html}</main>
        </body>
        </html>
        """
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user_email = request.session.get("user_email")
    cta = (
        '<a class="btn" href="/dashboard">Go to Dashboard</a>'
        if user_email
        else '<a class="btn" href="/signup">Create Free Account</a> <a class="btn" href="/login" style="background:#334155;">Login</a>'
    )
    return _page(
        "Home",
        user_email,
        f"""
        <h1>TaxClass Kenya</h1>
        <p>Practical Kenyan tax study notes, topic quizzes, and a 15-minute timed exam prep workspace.</p>
        <div class="card">
            <strong>Free Access:</strong> Browse study notes and take practice quizzes across 6 tax topics.<br/>
            <strong>Pro Access (KES {PLAN_PRICE_KES} / {PLAN_DAYS} days):</strong> Unlock the 15-minute timed exam mode.
        </div>
        {cta}
        """,
    )


@app.get("/signup", response_class=HTMLResponse)
def signup_get(request: Request, error: str | None = None):
    if request.session.get("user_email"):
        return RedirectResponse(url="/dashboard", status_code=303)
    err_html = f'<div class="notice">{html.escape(error)}</div>' if error else ""
    return _page(
        "Sign Up",
        None,
        f"""
        <h1>Create Student Account</h1>
        {err_html}
        <form method="post" action="/signup">
            <div><label>Full Name</label><br/><input type="text" name="full_name" required /></div>
            <div><label>Email</label><br/><input type="email" name="email" required /></div>
            <div><label>Password</label><br/><input type="password" name="password" minlength="6" required /></div>
            <div style="margin-top:12px;"><button class="btn" type="submit">Sign Up</button></div>
        </form>
        <p>Already have an account? <a href="/login">Log in</a>.</p>
        """,
    )


@app.post("/signup")
def signup_post(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    clean_name = full_name.strip()
    clean_email = email.strip().lower()
    if not clean_name or not clean_email or len(password) < 6:
        return RedirectResponse(
            url="/signup?error=" + quote("Provide name, valid email, and a 6+ character password."),
            status_code=303,
        )

    conn = _get_db_connection()
    try:
        existing = conn.execute("SELECT id FROM students WHERE email = ?", (clean_email,)).fetchone()
        if existing:
            return RedirectResponse(
                url="/signup?error=" + quote("An account with that email already exists."),
                status_code=303,
            )
        conn.execute(
            "INSERT INTO students (full_name, email, password_hash) VALUES (?, ?, ?)",
            (clean_name, clean_email, _hash_password(password)),
        )
        conn.commit()
    finally:
        conn.close()

    request.session["user_email"] = clean_email
    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request, error: str | None = None):
    if request.session.get("user_email"):
        return RedirectResponse(url="/dashboard", status_code=303)
    err_html = f'<div class="notice">{html.escape(error)}</div>' if error else ""
    return _page(
        "Login",
        None,
        f"""
        <h1>Student Login</h1>
        {err_html}
        <form method="post" action="/login">
            <div><label>Email</label><br/><input type="email" name="email" required /></div>
            <div><label>Password</label><br/><input type="password" name="password" required /></div>
            <div style="margin-top:12px;"><button class="btn" type="submit">Login</button></div>
        </form>
        <p>New to TaxClass Kenya? <a href="/signup">Create an account</a>.</p>
        """,
    )


@app.post("/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    clean_email = email.strip().lower()
    conn = _get_db_connection()
    try:
        row = conn.execute("SELECT * FROM students WHERE email = ?", (clean_email,)).fetchone()
    finally:
        conn.close()

    if not row or row["password_hash"] != _hash_password(password):
        return RedirectResponse(
            url="/login?error=" + quote("Invalid email or password."),
            status_code=303,
        )

    request.session.clear()
    request.session["user_email"] = row["email"]
    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/login", status_code=303)

    active = has_active_plan(user_email)
    expiry = get_plan_expiry(user_email)
    plan_text = f"Active Pro (expires {expiry})" if active else "Free Tier"
    attempts = get_student_attempts(user_email)

    rows_html = "".join(
        f"""
        <tr>
            <td>{html.escape(a['taken_at'])}</td>
            <td>{html.escape(a['mode'].title())}</td>
            <td>{html.escape(TOPIC_LABELS.get(a['topic_slug'], a['topic_slug']))}</td>
            <td>{a['score']} / {a['total']}</td>
        </tr>
        """
        for a in attempts
    )

    admin_link = (
        ' <a class="btn" href="/admin/payments" style="background:#334155;">Admin Payments</a>'
        if user_email.strip().lower() == ADMIN_EMAIL
        else ""
    )

    return _page(
        "Dashboard",
        user_email,
        f"""
        <h1>Student Dashboard</h1>
        <div class="card">
            <strong>Plan Status:</strong> {html.escape(plan_text)}<br/>
            <div style="margin-top:12px;">
                <a class="btn" href="/quiz">Practice Quiz</a>
                <a class="btn" href="/exam">15-Min Timed Exam</a>
                <a class="btn" href="/notes">Study Notes</a>
                <a class="btn" href="/upgrade">Upgrade Plan</a>
                {admin_link}
            </div>
        </div>
        <h2>Recent Attempts</h2>
        <table>
            <thead>
                <tr><th>Date</th><th>Mode</th><th>Topic</th><th>Score</th></tr>
            </thead>
            <tbody>{rows_html or "<tr><td colspan='4'>No attempts recorded yet.</td></tr>"}</tbody>
        </table>
        """,
    )


@app.get("/notes", response_class=HTMLResponse)
def notes_page(request: Request, topic: str = "all", q: str = ""):
    user_email = request.session.get("user_email")
    notes = get_notes(topic=topic, query=q)

    options_html = ['<option value="all">All Topics</option>']
    for slug, label in TOPIC_LABELS.items():
        selected = " selected" if topic == slug else ""
        options_html.append(f'<option value="{slug}"{selected}>{html.escape(label)}</option>')

    cards_html = []
    for n in notes:
        points_li = "".join(f"<li>{html.escape(pt)}</li>" for pt in n["key_points"])
        cards_html.append(
            f"""
            <div class="card">
                <h3>{html.escape(n['title'])} ({html.escape(n['tax_year'])})</h3>
                <p><strong>Topic:</strong> {html.escape(n['topic_name'])} — {html.escape(n['summary'])}</p>
                <ul>{points_li}</ul>
            </div>
            """
        )

    return _page(
        "Study Notes",
        user_email,
        f"""
        <h1>Kenyan Tax Study Notes</h1>
        <form method="get" action="/notes" style="margin-bottom:18px;">
            <select name="topic">{"".join(options_html)}</select>
            <input type="text" name="q" value="{html.escape(q)}" placeholder="Search notes..." />
            <button class="btn" type="submit">Filter</button>
        </form>
        {"".join(cards_html) or "<p>No matching study notes found.</p>"}
        """,
    )


def _render_quiz_form(
    user_email: str | None,
    mode: str,
    topic: str,
    questions: list[dict],
    action_url: str,
    timer_seconds: int | None = None,
) -> HTMLResponse:
    options_dropdown = ['<option value="all">All Topics</option>']
    for slug, label in TOPIC_LABELS.items():
        sel = " selected" if topic == slug else ""
        options_dropdown.append(f'<option value="{slug}"{sel}>{html.escape(label)}</option>')

    q_blocks = []
    for idx, q in enumerate(questions, start=1):
        choices = [
            ("A", q["option_a"]),
            ("B", q["option_b"]),
            ("C", q["option_c"]),
            ("D", q["option_d"]),
        ]
        radios = "".join(
            f"""
            <label style="display:block; margin:4px 0;">
                <input type="radio" name="q_{q['id']}" value="{opt_key}" />
                <strong>{opt_key}.</strong> {html.escape(opt_val)}
            </label>
            """
            for opt_key, opt_val in choices
        )
        q_blocks.append(
            f"""
            <div class="card">
                <p><strong>Q{idx}. [{html.escape(q['topic_name'])}]</strong> {html.escape(q['question_text'])}</p>
                {radios}
            </div>
            """
        )

    timer_script = ""
    timer_banner = ""
    if timer_seconds is not None:
        timer_banner = (
            f'<div class="notice"><strong>Time Remaining:</strong> <span id="timer">15:00</span></div>'
        )
        timer_script = f"""
        <script>
            let remaining = {timer_seconds};
            const el = document.getElementById("timer");
            const form = document.getElementById("quiz-form");
            function tick() {{
                const mins = String(Math.floor(remaining / 60)).padStart(2, "0");
                const secs = String(remaining % 60).padStart(2, "0");
                if (el) el.textContent = mins + ":" + secs;
                if (remaining <= 0) {{
                    if (form) form.submit();
                    return;
                }}
                remaining -= 1;
                setTimeout(tick, 1000);
            }}
            tick();
        </script>
        """

    heading = "Practice Quiz" if mode == "practice" else "15-Minute Timed Exam"
    filter_bar = (
        f"""
        <form method="get" action="/quiz" style="margin-bottom:16px;">
            <select name="topic">{"".join(options_dropdown)}</select>
            <button class="btn" type="submit">Load Topic</button>
        </form>
        """
        if mode == "practice"
        else ""
    )

    return _page(
        heading,
        user_email,
        f"""
        <h1>{html.escape(heading)}</h1>
        {timer_banner}
        {filter_bar}
        <form id="quiz-form" method="post" action="{action_url}">
            <input type="hidden" name="topic" value="{html.escape(topic)}" />
            {"".join(q_blocks)}
            <button class="btn" type="submit">Submit Answers</button>
        </form>
        {timer_script}
        """,
    )


async def _grade_submission(
    request: Request,
    mode: str,
    topic: str,
    questions: list[dict],
) -> HTMLResponse:
    form_data = await request.form()
    score = 0
    review_items = []

    for idx, q in enumerate(questions, start=1):
        field_name = f"q_{q['id']}"
        chosen = (form_data.get(field_name) or "").strip().upper()
        correct = q["correct_option"].strip().upper()
        is_right = chosen == correct
        if is_right:
            score += 1

        status_label = "Correct" if is_right else f"Incorrect (Your answer: {chosen or 'None'}, Correct: {correct})"
        review_items.append(
            f"""
            <div class="card">
                <p><strong>Q{idx}.</strong> {html.escape(q['question_text'])}</p>
                <p><strong>{html.escape(status_label)}</strong></p>
                <p>{html.escape(q['explanation'])}</p>
            </div>
            """
        )

    user_email = request.session.get("user_email")
    if user_email:
        save_attempt(
            student_email=user_email,
            mode=mode,
            topic_slug=topic,
            score=score,
            total=len(questions),
        )

    return _page(
        "Quiz Results",
        user_email,
        f"""
        <h1>Results — {html.escape(mode.title())}</h1>
        <div class="card"><strong>Score:</strong> {score} / {len(questions)}</div>
        {"".join(review_items)}
        <a class="btn" href="/dashboard">Back to Dashboard</a>
        """,
    )


@app.get("/quiz", response_class=HTMLResponse)
def quiz_get(request: Request, topic: str = "all"):
    user_email = request.session.get("user_email")
    questions = get_questions(topic=topic)
    return _render_quiz_form(
        user_email=user_email,
        mode="practice",
        topic=topic,
        questions=questions,
        action_url="/quiz",
    )


@app.post("/quiz", response_class=HTMLResponse)
async def quiz_post(request: Request, topic: str = Form("all")):
    questions = get_questions(topic=topic)
    return await _grade_submission(request=request, mode="practice", topic=topic, questions=questions)


@app.get("/exam", response_class=HTMLResponse)
def exam_get(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/login", status_code=303)
    if not has_active_plan(user_email):
        return RedirectResponse(url="/upgrade", status_code=303)

    questions = get_questions(topic="all")[:EXAM_MAX_QUESTIONS]
    return _render_quiz_form(
        user_email=user_email,
        mode="exam",
        topic="all",
        questions=questions,
        action_url="/exam",
        timer_seconds=EXAM_DURATION_SECONDS,
    )


@app.post("/exam", response_class=HTMLResponse)
async def exam_post(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/login", status_code=303)
    if not has_active_plan(user_email):
        return RedirectResponse(url="/upgrade", status_code=303)

    questions = get_questions(topic="all")[:EXAM_MAX_QUESTIONS]
    return await _grade_submission(request=request, mode="exam", topic="all", questions=questions)


@app.get("/upgrade", response_class=HTMLResponse)
def upgrade_page(request: Request, msg: str | None = None):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/login", status_code=303)

    active = has_active_plan(user_email)
    expiry = get_plan_expiry(user_email)
    status_badge = f"Active Pro (expires {expiry})" if active else "Free Tier"
    notice = f'<div class="notice">{html.escape(msg)}</div>' if msg else ""

    return _page(
        "Upgrade",
        user_email,
        f"""
        <h1>Upgrade to Pro Access</h1>
        {notice}
        <div class="card">
            <p><strong>Account:</strong> {html.escape(user_email)}</p>
            <p><strong>Current Status:</strong> {html.escape(status_badge)}</p>
            <p>
                Send <strong>KES {PLAN_PRICE_KES}</strong> via M-Pesa to
                <strong>{html.escape(MPESA_NUMBER_LOCAL)}</strong>
                (<em>{html.escape(MPESA_NUMBER_INTL)}</em>) for
                <strong>{PLAN_DAYS} days</strong> of timed exam access, then submit your M-Pesa confirmation code below:
            </p>
            <form method="post" action="/upgrade">
                <input type="text" name="mpesa_code" placeholder="e.g. SLK89X21PQ" required />
                <button class="btn" type="submit">Submit Payment Code</button>
            </form>
        </div>
        """,
    )


@app.post("/upgrade")
def upgrade_post(request: Request, mpesa_code: str = Form(...)):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/login", status_code=303)

    _, message = submit_payment(
        student_email=user_email,
        mpesa_code=mpesa_code,
        amount=PLAN_PRICE_KES,
    )
    return RedirectResponse(url="/upgrade?msg=" + quote(message), status_code=303)


@app.get("/admin/payments", response_class=HTMLResponse)
def admin_payments_page(request: Request):
    user_email = (request.session.get("user_email") or "").strip().lower()
    if user_email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Admin access required")

    rows = list_payments()
    table_rows = "".join(
        f"""
        <tr>
            <td>{r['id']}</td>
            <td>{html.escape(r['student_email'])}</td>
            <td>{html.escape(r['mpesa_code'])}</td>
            <td>KES {r['amount']}</td>
            <td>{html.escape(r['status'])}</td>
            <td>
                <form method="post" action="/admin/payments/{r['id']}/approve" style="display:inline;">
                    <button class="btn" type="submit">Approve ({PLAN_DAYS}d)</button>
                </form>
            </td>
        </tr>
        """
        for r in rows
    )

    return _page(
        "Admin Payments",
        user_email,
        f"""
        <h1>Payment Submissions</h1>
        <table>
            <thead>
                <tr><th>ID</th><th>Student</th><th>M-Pesa Code</th><th>Amount</th><th>Status</th><th>Action</th></tr>
            </thead>
            <tbody>{table_rows or "<tr><td colspan='6'>No payments submitted yet.</td></tr>"}</tbody>
        </table>
        """,
    )


@app.post("/admin/payments/{payment_id}/approve")
def admin_approve_payment_route(request: Request, payment_id: int):
    user_email = (request.session.get("user_email") or "").strip().lower()
    if user_email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Admin access required")

    approve_payment(payment_id=payment_id, days=PLAN_DAYS)
    return RedirectResponse(url="/admin/payments", status_code=303)