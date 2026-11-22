JOB_POSTINGS = [
    {"role": "Tax Associate", "company": "Rift Valley Advisory", "location": "Nanyuki"},
    {"role": "Junior Accountant", "company": "Nairobi Ledger Ltd", "location": "Nairobi"},
]

@app.get("/jobs", response_class=HTMLResponse)
def jobs_page():
    items = "".join(
        f"<li><strong>{job['role']}</strong> — {job['company']} ({job['location']})</li>"
        for job in JOB_POSTINGS
    )
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>TaxClass Kenya Job Network</title></head>
    <body>
        <h1>Job Network</h1>
        <form action="/jobs" method="post">
            <input name="role" placeholder="Role (e.g., Audit Trainee)" required />
            <input name="company" placeholder="Company" required />
            <input name="location" placeholder="Location" required />
            <button type="submit">Post Job</button>
        </form>
        <h2>Available Roles</h2>
        <ul>{items}</ul>
    </body>
    </html>
    """

@app.post("/jobs")
def create_job(
    role: str = Form(...),
    company: str = Form(...),
    location: str = Form(...),
):
    JOB_POSTINGS.append({"role": role, "company": company, "location": location})
    return RedirectResponse(url="/jobs", status_code=303)

from fastapi import Form
from fastapi.responses import HTMLResponse, RedirectResponse

import base64
import hashlib
import hmac
import importlib
import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.context import CryptContext

import database

load_dotenv()

app = FastAPI(title="Financial & Taxation Accounts")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-in-production")
SESSION_COOKIE_NAME = "tax_finance_session"

OWNER_NAME = os.getenv("OWNER_NAME", "Kelvin Koinange").strip()
OWNER_PHONE = os.getenv("OWNER_PHONE", "0700566525").strip()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "koinangekelvin615@gmail.com").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "kelvin00@")

STUDENT_EMAIL = os.getenv("STUDENT_EMAIL", "student@example.com").strip().lower()
STUDENT_PASSWORD = os.getenv("STUDENT_PASSWORD", "Student123!")

CHALLENGE_BLOCK_SIZE = 50
CHALLENGE_SECONDS_PER_BLOCK = 2 * 3600 + 30 * 60
POINTS_PER_CHALLENGE_QUESTION = 2

BUILTIN_FINANCE_TAX_NOTES: list[dict] = [
    {
        "topic": "Financial Statements",
        "category": "Financial Accounting",
        "summary": "Theory of accounting conventions, financial statements, and ratios alongside worked profit and liquidity computations.",
        "points": [
            "Theory: The Statement of Profit or Loss measures performance over a period; the Statement of Financial Position reports assets, liabilities, and capital at a point in time.",
            "Theory: Accruals, going concern, consistency, and prudence govern proper recognition and valuation.",
            "Calculation 1 (Gross Profit): Opening stock (KES 60,000) + Purchases (KES 230,000) - Closing stock (KES 50,000) = Cost of sales (KES 240,000); Sales (KES 480,000) - Cost of sales (KES 240,000) = KES 240,000 gross profit.",
            "Calculation 2 (Current Ratio): Current assets (KES 270,000) / Current liabilities (KES 150,000) = 1.80.",
        ],
        "formula_or_rule": "Gross Profit = Sales - (Opening Stock + Purchases - Closing Stock)  |  Current Ratio = Current Assets / Current Liabilities",
    },
    {
        "topic": "PAYE & Income Tax",
        "category": "Taxation Accounts",
        "summary": "Theory of employment income (PAYE), allowable deductions, tax bands, and reliefs with worked net PAYE calculations.",
        "points": [
            "Theory: Gross emoluments include salary, taxable allowances, and taxable benefits before allowable deductions.",
            "Theory: Allowable reliefs (such as personal relief of KES 2,400/month and qualifying insurance/SHIF relief) are deducted from gross tax payable.",
            "Calculation 1 (Taxable Pay): Gross salary (KES 120,000) - Allowable deductions (KES 14,500) = KES 105,500 taxable pay.",
            "Calculation 2 (Net PAYE): Gross tax (KES 46,800) - Personal relief (KES 2,400) - Insurance relief (KES 1,200) = KES 43,200 net PAYE.",
        ],
        "formula_or_rule": "Taxable Pay = Gross Emoluments - Allowable Deductions  |  Net PAYE = Gross Tax - Allowable Reliefs",
    },
    {
        "topic": "VAT & Indirect Taxes",
        "category": "Taxation Accounts",
        "summary": "Theory of output VAT, input VAT, standard/zero-rated/exempt supplies, eTIMS invoicing, and worked VAT calculations.",
        "points": [
            "Theory: Output VAT is charged on taxable supplies; input VAT is incurred on eligible business purchases.",
            "Theory: Zero-rated supplies carry a 0% output rate with input VAT recovery; exempt supplies carry no output VAT and disallow input VAT recovery.",
            "Calculation 1 (Output VAT at 16%): 16% x KES 250,000 VAT-exclusive sales = KES 40,000 output VAT (KES 290,000 inclusive).",
            "Calculation 2 (Net VAT Payable): Output VAT (KES 176,000) - Allowable input VAT (KES 112,500) = KES 63,500 net VAT payable.",
        ],
        "formula_or_rule": "Output VAT = Rate x Taxable Value (16% standard)  |  Net VAT = Output VAT - Allowable Input VAT",
    },
    {
        "topic": "Turnover Tax",
        "category": "Taxation Accounts",
        "summary": "Theory of Turnover Tax (TOT) eligibility, gross turnover base, final-tax treatment, and worked TOT calculations.",
        "points": [
            "Theory: TOT applies to qualifying businesses whose gross turnover is between KES 1,000,000 and KES 25,000,000 per year.",
            "Theory: TOT is charged on gross turnover without expense deductions and operates as a final tax on qualifying turnover.",
            "Calculation 1: 1.5% x KES 800,000 gross sales = KES 12,000 TOT.",
            "Calculation 2: 1.5% x KES 1,400,000 gross sales = KES 21,000 TOT (expenses are not deducted from the TOT base).",
        ],
        "formula_or_rule": "Turnover Tax = 1.5% x Gross Turnover (e.g. 1.5% x 800,000 = KES 12,000)",
    },
    {
        "topic": "Withholding Tax",
        "category": "Taxation Accounts",
        "summary": "Theory of withholding tax at source, resident vs. non-resident rates, credit vs. final tax, and worked net payments.",
        "points": [
            "Theory: Withholding agents deduct WHT at source from qualifying payments and remit it to the tax authority.",
            "Theory: For residents, WHT is generally credited against income tax liability (or final where specified), whereas for non-residents it is typically a final tax.",
            "Calculation 1 (5% Consultancy WHT): 5% x KES 200,000 = KES 10,000 WHT; Net payment = KES 190,000.",
            "Calculation 2 (3% Contractor WHT): 3% x KES 350,000 = KES 10,500 WHT; Net payment = KES 339,500.",
        ],
        "formula_or_rule": "Withholding Tax = WHT Rate x Gross Qualifying Payment  |  Net Payment = Gross Payment - WHT",
    },
    {
        "topic": "Capital Gains Tax",
        "category": "Taxation Accounts",
        "summary": "Theory of Capital Gains Tax (CGT), net gain computation, adjusted cost, and worked 15% CGT calculations.",
        "points": [
            "Theory: CGT is charged on the net realized gain from transferring property/chargeable assets, not on gross proceeds.",
            "Theory: Net gain deducts adjusted cost (purchase price plus allowable improvement and acquisition/transfer costs) from net transfer proceeds.",
            "Calculation 1: Proceeds (KES 8,000,000) - (Cost KES 5,000,000 + Improvements/Costs KES 500,000) = KES 2,500,000 net gain; 15% CGT = KES 375,000.",
            "Calculation 2: Proceeds (KES 3,200,000) - (Cost KES 2,100,000 + Incidental costs KES 100,000) = KES 1,000,000 net gain; 15% CGT = KES 150,000.",
        ],
        "formula_or_rule": "Net Gain = Net Transfer Proceeds - Adjusted Cost  |  CGT Payable = 15% x Net Gain",
    },
]

APP_STYLES = """
    * { box-sizing: border-box; }
    body {
        font-family: "Segoe UI", Arial, sans-serif;
        max-width: 1100px;
        margin: 0 auto;
        padding: 24px 20px 64px;
        background: #f1f5f9;
        color: #0f172a;
        line-height: 1.5;
    }
    a { color: #1d4ed8; }
    .topbar {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        background: #ffffff;
        padding: 16px 20px;
        border-radius: 10px;
        border: 1px solid #cbd5e1;
        margin-bottom: 12px;
    }
    .brand-title { margin: 0; font-size: 1.45rem; color: #0f172a; }
    .brand-sub { margin: 2px 0 0; font-size: 0.9rem; color: #475569; }
    .user-meta { font-size: 0.9rem; color: #334155; }
    .pill {
        display: inline-block;
        padding: 2px 9px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        background: #dbeafe;
        color: #1e40af;
    }
    .notice-banner {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1e3a8a;
        padding: 10px 16px;
        border-radius: 8px;
        margin-bottom: 14px;
        font-size: 0.92rem;
    }
    .tab-bar {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        overflow-x: auto;
        gap: 8px;
        background: #ffffff;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid #cbd5e1;
        margin-bottom: 20px;
    }
    .tab-link {
        text-decoration: none;
        padding: 9px 16px;
        border-radius: 8px;
        background: #f1f5f9;
        color: #334155;
        font-weight: 600;
        font-size: 0.92rem;
        white-space: nowrap;
    }
    .tab-link:hover { background: #e2e8f0; color: #0f172a; }
    .tab-link.active { background: #1d4ed8; color: #ffffff; }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 14px;
        margin-bottom: 20px;
    }
    .stat-card {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 16px;
    }
    .stat-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b; font-weight: 700; }
    .stat-value { font-size: 1.45rem; font-weight: 700; color: #0f172a; margin: 4px 0; }
    .stat-note { font-size: 0.85rem; color: #475569; }
    .progress-track {
        width: 100%;
        height: 9px;
        background: #e2e8f0;
        border-radius: 999px;
        overflow: hidden;
        margin-top: 8px;
    }
    .progress-fill { height: 100%; background: #16a34a; border-radius: 999px; }
    section {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    section h2 { margin-top: 0; font-size: 1.2rem; color: #0f172a; }
    .toolbar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 12px 14px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
        margin-bottom: 12px;
    }
    .form-field label { display: block; font-weight: 600; font-size: 0.88rem; margin-bottom: 4px; }
    .form-field input, .form-field select, .form-field textarea {
        width: 100%;
        padding: 8px 10px;
        border: 1px solid #94a3b8;
        border-radius: 6px;
        background: #ffffff;
        font-family: inherit;
        font-size: 0.92rem;
    }
    .note-card {
        border: 1px solid #cbd5e1;
        border-left: 4px solid #1d4ed8;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 14px;
        background: #f8fafc;
    }
    .note-header { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px; }
    .note-title { font-size: 1.08rem; font-weight: 700; color: #0f172a; }
    .badge {
        display: inline-block;
        font-size: 0.78rem;
        padding: 2px 9px;
        border-radius: 999px;
        background: #e2e8f0;
        color: #1e293b;
        font-weight: 600;
        margin-left: 6px;
    }
    .note-points { margin: 8px 0 12px 20px; }
    .note-points li { margin-bottom: 5px; }
    .note-formula {
        padding: 10px 12px;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 6px;
        font-size: 0.92rem;
        color: #1e3a8a;
    }
    .q-card {
        margin-bottom: 14px;
        padding: 14px 16px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        background: #f8fafc;
    }
    .q-meta { font-size: 0.82rem; color: #475569; margin-bottom: 4px; font-weight: 600; }
    .q-title { font-size: 1rem; margin-bottom: 10px; color: #0f172a; }
    .tick-opt {
        display: flex;
        align-items: center;
        padding: 9px 12px;
        margin: 6px 0;
        border-radius: 6px;
        cursor: pointer;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        font-size: 0.95rem;
    }
    .tick-opt:hover { background: #eff6ff; border-color: #93c5fd; }
    .tick-opt input { margin-right: 10px; transform: scale(1.15); cursor: pointer; }
    .timer-bar {
        position: sticky;
        top: 8px;
        background: #0f172a;
        color: #ffffff;
        padding: 14px 18px;
        border-radius: 10px;
        margin-bottom: 18px;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        z-index: 20;
    }
    .timer-clock {
        font-size: 1.25rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        background: #1e293b;
        padding: 4px 12px;
        border-radius: 6px;
    }
    .review-ok { color: #15803d; font-weight: 700; }
    .review-bad { color: #b91c1c; font-weight: 700; }
    select, input[type="text"], input[type="email"], input[type="password"] {
        padding: 8px 11px;
        border: 1px solid #94a3b8;
        border-radius: 6px;
        background: #ffffff;
        color: #0f172a;
        font-size: 0.92rem;
    }
    .btn {
        display: inline-block;
        padding: 9px 16px;
        border-radius: 7px;
        border: none;
        background: #1d4ed8;
        color: #ffffff;
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        text-decoration: none;
    }
    .btn:hover { background: #1e40af; }
    .btn-secondary { background: #e2e8f0; color: #0f172a; }
    .btn-secondary:hover { background: #cbd5e1; }
    .btn-sm { padding: 5px 11px; font-size: 0.82rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }
    th, td { text-align: left; padding: 9px 11px; border-bottom: 1px solid #e2e8f0; }
    th { background: #f8fafc; color: #334155; font-weight: 700; }
    .auth-grid {
        max-width: 820px;
        margin: 40px auto;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
        gap: 20px;
    }
    .auth-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #cbd5e1;
    }
    .auth-card label { display: block; margin-top: 12px; font-weight: 600; font-size: 0.9rem; }
    .auth-card input { width: 100%; margin-top: 4px; }
    .auth-card button { width: 100%; margin-top: 16px; }
    .owner-box {
        margin-top: 14px;
        padding: 12px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        font-size: 0.84rem;
        color: #475569;
    }
"""


@app.on_event("startup")
def on_startup():
    admin_seed = {
        "email": ADMIN_EMAIL,
        "name": OWNER_NAME,
        "phone": OWNER_PHONE,
        "password_hash": pwd_context.hash(ADMIN_PASSWORD),
    }
    student_seed = {
        "email": STUDENT_EMAIL,
        "name": "Student Learner",
        "phone": "254712345678",
        "password_hash": pwd_context.hash(STUDENT_PASSWORD),
    }
    database.init_db(admin_seed=admin_seed, student_seed=student_seed)


def create_session_token(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded = base64.urlsafe_b64encode(raw).decode("utf-8")
    sig = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded}.{sig}"


def read_session_token(token: str | None) -> dict | None:
    if not token or "." not in token:
        return None
    encoded, sig = token.rsplit(".", 1)
    expected_sig = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None
    try:
        raw = base64.urlsafe_b64decode(encoded.encode("utf-8"))
        data = json.loads(raw.decode("utf-8"))
        if isinstance(data, dict) and "email" in data and "role" in data:
            return data
    except Exception:
        return None
    return None


def get_current_user(request: Request) -> dict | None:
    session = read_session_token(request.cookies.get(SESSION_COOKIE_NAME))
    if not session:
        return None
    db_user = database.get_user_by_email(session["email"])
    if db_user:
        return {
            "email": db_user["email"],
            "name": db_user["name"],
            "phone": db_user["phone"],
            "role": db_user["role"],
            "subscription_status": db_user["subscription_status"],
        }
    return session


def verify_login(email: str, password: str) -> dict | None:
    account = database.get_user_by_email(email)
    if not account:
        return None
    if not pwd_context.verify(password, account["password_hash"]):
        return None
    return {
        "email": account["email"],
        "name": account["name"],
        "phone": account["phone"],
        "role": account["role"],
    }


def load_module_items(module_name: str, names: list[str]) -> list:
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        return []
    for name in names:
        val = getattr(mod, name, None)
        if callable(val):
            try:
                out = val()
                if isinstance(out, list):
                    return out
            except Exception:
                pass
        elif isinstance(val, list):
            return val
        elif isinstance(val, dict):
            return list(val.values())
    return []


def get_all_notes() -> list[dict]:
    ext_notes = load_module_items("tax_notes", ["NOTES", "notes", "TAX_NOTES", "get_notes"])
    combined: list[dict] = []
    seen_topics: set[str] = set()

    for n in ext_notes:
        if isinstance(n, dict):
            combined.append(n)
            if n.get("topic"):
                seen_topics.add(str(n["topic"]).lower())

    for n in BUILTIN_FINANCE_TAX_NOTES:
        if str(n.get("topic", "")).lower() not in seen_topics:
            combined.append(n)
            seen_topics.add(str(n["topic"]).lower())

    for n in database.get_custom_notes():
        combined.append(n)

    return combined


def get_all_questions() -> list[dict]:
    ext_qs = load_module_items("quiz", ["QUESTIONS", "questions", "get_questions"])
    combined: list[dict] = [q for q in ext_qs if isinstance(q, dict)]
    combined.extend(database.get_custom_questions(start_id=len(combined) + 1))
    return combined


def filter_by_topic(items: list, selected_topic: str) -> list:
    if not selected_topic or selected_topic == "All":
        return items
    return [
        item for item in items
        if isinstance(item, dict) and str(item.get("topic", "")).lower() == selected_topic.lower()
    ]


def topic_counts(questions: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for q in questions:
        if isinstance(q, dict):
            t = q.get("topic", "General")
            counts[t] = counts.get(t, 0) + 1
    return counts


def build_topic_select(options: list[str], selected: str, select_id: str, select_name: str) -> str:
    seen: list[str] = []
    for opt in options:
        if opt and opt.lower() not in {x.lower() for x in seen}:
            seen.append(opt)
    opts_html = "".join(
        f"<option value=\"{t}\" {'selected' if t.lower() == selected.lower() else ''}>{t}</option>"
        for t in seen
    )
    return f"<select id='{select_id}' name='{select_name}'>{opts_html}</select>"


def render_horizontal_tabs(base_path: str, active_tab: str, is_admin: bool) -> str:
    tabs = [
        ("overview", "Overview", f"{base_path}?tab=overview"),
        ("notes", "Tax & Finance Notes", f"{base_path}?tab=notes"),
        ("questions", "Practice Questions", f"{base_path}?tab=questions"),
        ("challenge", "50-Q Challenge", "/challenge"),
        ("payments", "Payments", f"{base_path}?tab=payments"),
    ]
    if is_admin:
        tabs.append(("manage", "Owner Controls", "/admin?tab=manage"))

    links = "".join(
        f"<a class='tab-link {'active' if key == active_tab else ''}' href='{url}'>{label}</a>"
        for key, label, url in tabs
    )
    return f"<nav class='tab-bar' aria-label='Workspace sections'>{links}</nav>"


def render_shell(user: dict, page_title: str, active_tab: str, body_html: str) -> str:
    is_admin = user["role"] == "admin"
    base_path = "/admin" if is_admin else "/student"
    role_badge = "Owner / Admin" if is_admin else "Student"
    announcement = database.get_announcement()
    tabs_html = render_horizontal_tabs(base_path, active_tab, is_admin=is_admin)

    banner_html = (
        f"<div class='notice-banner'><strong>Platform Notice:</strong> {announcement}</div>"
        if announcement
        else ""
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>{page_title} — Financial &amp; Taxation Accounts</title>
        <style>{APP_STYLES}</style>
    </head>
    <body>
        <header class="topbar">
            <div>
                <h1 class="brand-title">{page_title}</h1>
                <p class="brand-sub">Financial &amp; Taxation Accounts • Study Notes, Topic Drills &amp; 50-Q Timed Challenge (2 pts each = 100 pts)</p>
            </div>
            <div class="user-meta">
                <span class="pill">{role_badge}</span>
                <strong>{user["name"]}</strong> ({user["email"]}) |
                <a href="/logout">Sign out</a>
            </div>
        </header>
        {banner_html}
        {tabs_html}
        <main>{body_html}</main>
    </body>
    </html>
    """


def format_note(note, base_path: str) -> str:
    if isinstance(note, dict) and "topic" in note and "summary" in note:
        topic = note.get("topic", "Topic")
        category = note.get("category", "")
        summary = note.get("summary", "")
        points = note.get("points", [])
        formula = note.get("formula_or_rule", "")

        cat_badge = f"<span class='badge'>{category}</span>" if category else ""
        pts_html = (
            "<ul class='note-points'>" + "".join(f"<li>{p}</li>" for p in points) + "</ul>"
            if points
            else ""
        )
        formula_html = (
            f"<div class='note-formula'><strong>Key Rule / Formula:</strong> {formula}</div>"
            if formula
            else ""
        )
        practice_btn = (
            f"<a class='btn btn-secondary btn-sm' href='{base_path}?tab=questions&topic={topic}'>"
            f"Practice {topic}</a>"
        )
        return (
            f"<article class='note-card'>"
            f"<div class='note-header'>"
            f"<div class='note-title'>{topic}{cat_badge}</div>"
            f"<div>{practice_btn}</div>"
            f"</div>"
            f"<p>{summary}</p>"
            f"{pts_html}"
            f"{formula_html}"
            f"</article>"
        )
    if isinstance(note, dict):
        parts = ", ".join(f"<strong>{k}:</strong> {v}" for k, v in note.items())
        return f"<article class='note-card'>{parts}</article>"
    return f"<article class='note-card'>{note}</article>"


def format_tickable_question_admin(q) -> str:
    if not isinstance(q, dict):
        return f"<li class='q-card'>{q}</li>"
    qid = q.get("id", "")
    topic = q.get("topic", "General")
    text = q.get("question", "")
    options = q.get("options", [])
    opts_html = "".join(
        f"<label class='tick-opt'>"
        f"<input type='checkbox' name='admin_q_{qid}' value='{opt[:1]}' /> {opt}"
        f"</label>"
        for opt in options
    )
    return (
        f"<li class='q-card'>"
        f"<div class='q-meta'>Question #{qid} • Topic: {topic}</div>"
        f"<div class='q-title'><strong>{text}</strong></div>"
        f"<div>{opts_html}</div>"
        f"</li>"
    )


def format_answer_key_item(q) -> str:
    if not isinstance(q, dict):
        return f"<li>{q}</li>"
    qid = q.get("id", "")
    topic = q.get("topic", "General")
    ans = q.get("answer", "")
    exp = q.get("explanation", "")
    return (
        f"<li style='margin-bottom: 10px;'>"
        f"<strong>#{qid} [{topic}]</strong> — Answer: <span class='review-ok'>{ans}</span>"
        f"{f' — <em>{exp}</em>' if exp else ''}"
        f"</li>"
    )


def get_challenge_block(block: int = 1) -> tuple[list[dict], int, int]:
    all_challenge = load_module_items("quiz", ["CHALLENGE_QUESTIONS", "get_challenge_questions"])
    if not all_challenge:
        base_qs = get_all_questions()
        by_topic: dict[str, list[dict]] = {}
        for q in base_qs:
            if isinstance(q, dict):
                by_topic.setdefault(q.get("topic", "General"), []).append(q)
        max_len = max((len(v) for v in by_topic.values()), default=0)
        for idx in range(max_len):
            for t in by_topic:
                if idx < len(by_topic[t]):
                    all_challenge.append(by_topic[t][idx])

    total_blocks = max(1, (len(all_challenge) + CHALLENGE_BLOCK_SIZE - 1) // CHALLENGE_BLOCK_SIZE)
    current_block = max(1, min(block, total_blocks))
    start = (current_block - 1) * CHALLENGE_BLOCK_SIZE
    end = start + CHALLENGE_BLOCK_SIZE
    return all_challenge[start:end], current_block, total_blocks


def build_overview_section(user: dict, base_path: str) -> str:
    notes = get_all_notes()
    questions = get_all_questions()
    counts = topic_counts(questions)
    prog = database.get_user_progress_summary(user["email"])

    practice_pct = (
        round(prog["practice_correct"] / prog["practice_total"] * 100, 1)
        if prog["practice_total"] > 0
        else 0.0
    )
    challenge_pct = (
        round(prog["challenge_points"] / prog["challenge_max_points"] * 100, 1)
        if prog["challenge_max_points"] > 0
        else 0.0
    )

    topic_rows = "".join(
        f"<tr>"
        f"<td><strong>{t}</strong></td>"
        f"<td>{c} questions</td>"
        f"<td><a class='btn btn-secondary btn-sm' href='{base_path}?tab=questions&topic={t}'>Practice Topic</a> "
        f"<a class='btn btn-secondary btn-sm' href='{base_path}?tab=notes&note_topic={t}'>Read Notes</a></td>"
        f"</tr>"
        for t, c in counts.items()
    ) or "<tr><td colspan='3'>No topics loaded yet.</td></tr>"

    history_rows = "".join(
        f"<tr>"
        f"<td>{h.get('date', '-')}</td>"
        f"<td>{h.get('mode', '-')}</td>"
        f"<td>{h.get('detail', '-')}</td>"
        f"<td><strong>{h.get('score', '-')}</strong></td>"
        f"</tr>"
        for h in prog.get("history", [])
    ) or "<tr><td colspan='4'>Complete a practice quiz or 50-question challenge to log scores here.</td></tr>"

    return f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Practice Accuracy</div>
            <div class="stat-value">{practice_pct}%</div>
            <div class="stat-note">{prog["practice_correct"]} / {prog["practice_total"]} correct ({prog["practice_runs"]} run(s))</div>
            <div class="progress-track"><div class="progress-fill" style="width: {min(100, practice_pct)}%;"></div></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">50-Q Challenge Score</div>
            <div class="stat-value">{prog["challenge_points"]} pts</div>
            <div class="stat-note">Out of {prog["challenge_max_points"]} max pts ({challenge_pct}% • {prog["challenge_runs"]} run(s))</div>
            <div class="progress-track"><div class="progress-fill" style="width: {min(100, challenge_pct)}%;"></div></div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Study Library</div>
            <div class="stat-value">{len(notes)} Notes / {len(questions)} Qs</div>
            <div class="stat-note">{len(counts)} financial &amp; tax topics</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Account &amp; Latest Activity</div>
            <div class="stat-value" style="font-size: 1rem;">{prog["last_activity"]}</div>
            <div class="stat-note">Access: <strong>{user.get("subscription_status", "Active")}</strong> • <a href="/challenge">Start Challenge</a></div>
        </div>
    </div>

    <section>
        <h2>Topics &amp; Study Paths</h2>
        <table>
            <thead>
                <tr>
                    <th>Topic</th>
                    <th>Questions</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>{topic_rows}</tbody>
        </table>
    </section>

    <section>
        <h2>Recent Assessment Log</h2>
        <table>
            <thead>
                <tr>
                    <th>Date &amp; Time</th>
                    <th>Mode</th>
                    <th>Topic / Block</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>{history_rows}</tbody>
        </table>
    </section>
    """


def build_payments_section(user: dict, base_path: str, status_message: str = "") -> str:
    is_admin = user["role"] == "admin"
    payments = database.list_payments()
    if not is_admin:
        payments = [p for p in payments if p["user_email"].lower() == user["email"].lower()]

    banner = (
        f"<div class='note-formula' style='margin-bottom: 14px;'><strong>Update:</strong> {status_message}</div>"
        if status_message
        else ""
    )

    rows_html = ""
    for p in payments:
        action_cell = ""
        if is_admin:
            action_cell = (
                f"<td>"
                f"<form method='post' action='/admin/payments/{p['id']}/status' style='display:inline;'>"
                f"<input type='hidden' name='status' value='Confirmed' />"
                f"<button type='submit' class='btn btn-sm'>Approve</button>"
                f"</form> "
                f"<form method='post' action='/admin/payments/{p['id']}/status' style='display:inline;'>"
                f"<input type='hidden' name='status' value='Rejected' />"
                f"<button type='submit' class='btn btn-secondary btn-sm'>Reject</button>"
                f"</form>"
                f"</td>"
            )
        rows_html += (
            f"<tr>"
            f"<td><strong>{p['reference']}</strong></td>"
            f"<td>{p['user_email']}</td>"
            f"<td>{p['phone']}</td>"
            f"<td>{p['plan']}</td>"
            f"<td><strong>{p['amount']}</strong></td>"
            f"<td><span class='pill'>{p['status']}</span></td>"
            f"<td>{p['created_at']}</td>"
            f"{action_cell}"
            f"</tr>"
        )

    if not rows_html:
        cols = 8 if is_admin else 7
        rows_html = f"<tr><td colspan='{cols}'>No payment records yet.</td></tr>"

    admin_th = "<th>Owner Actions</th>" if is_admin else ""

    return f"""
    <section>
        <h2>Subscription &amp; M-Pesa Payment Records</h2>
        <div class="note-formula" style="margin-bottom: 14px;">
            <strong>How to Pay (KES 500 / 30 Days):</strong> Send <strong>KES 500</strong> via M-Pesa to
            <strong>{OWNER_PHONE}</strong> ({OWNER_NAME}), then enter your M-Pesa confirmation code below so your access can be activated.
        </div>
        {banner}
        <form method="post" action="/payments/record" class="toolbar">
            <input type="hidden" name="return_to" value="{base_path}?tab=payments" />
            <div>
                <label for="phone"><strong>Phone:</strong></label>
                <input type="text" id="phone" name="phone" value="{OWNER_PHONE}" placeholder="{OWNER_PHONE}" required />
            </div>
            <div>
                <label for="reference"><strong>M-Pesa Code:</strong></label>
                <input type="text" id="reference" name="reference" placeholder="e.g. MPX123ABC" required />
            </div>
            <div>
                <label for="plan"><strong>Plan:</strong></label>
                <select id="plan" name="plan">
                    <option value="30-Day Full Access (KES 500)">30-Day Full Access (KES 500)</option>
                    <option value="Exam & Challenge Pack (KES 500)">Exam &amp; Challenge Pack (KES 500)</option>
                </select>
            </div>
            <button type="submit" class="btn">Submit Payment</button>
        </form>
    </section>

    <section>
        <h2>Payment Ledger ({len(payments)})</h2>
        <table>
            <thead>
                <tr>
                    <th>Reference</th>
                    <th>Account</th>
                    <th>Phone</th>
                    <th>Plan</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Date</th>
                    {admin_th}
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </section>
    """


def build_owner_controls_section(status_message: str = "") -> str:
    users = database.list_all_users()
    payments = database.list_payments()
    confirmed_count = sum(1 for p in payments if p["status"] == "Confirmed")
    pending_count = sum(1 for p in payments if p["status"] == "Submitted")
    announcement = database.get_announcement()

    banner = (
        f"<div class='note-formula' style='margin-bottom: 14px;'><strong>Owner Action:</strong> {status_message}</div>"
        if status_message
        else ""
    )

    user_rows = "".join(
        f"<tr>"
        f"<td><strong>{u['name']}</strong></td>"
        f"<td>{u['email']}</td>"
        f"<td>{u['phone'] or '-'}</td>"
        f"<td><span class='pill'>{u['role']}</span></td>"
        f"<td><strong>{u['subscription_status']}</strong></td>"
        f"<td>"
        f"<form method='post' action='/admin/users/subscription' style='display:inline;'>"
        f"<input type='hidden' name='email' value='{u['email']}' />"
        f"<input type='hidden' name='status' value='Active' />"
        f"<button type='submit' class='btn btn-sm'>Activate</button>"
        f"</form> "
        f"<form method='post' action='/admin/users/subscription' style='display:inline;'>"
        f"<input type='hidden' name='email' value='{u['email']}' />"
        f"<input type='hidden' name='status' value='Pending' />"
        f"<button type='submit' class='btn btn-secondary btn-sm'>Set Pending</button>"
        f"</form>"
        f"</td>"
        f"</tr>"
        for u in users
    )

    return f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Registered Accounts</div>
            <div class="stat-value">{len(users)}</div>
            <div class="stat-note">Owner: {OWNER_NAME} ({OWNER_PHONE})</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Confirmed Payments</div>
            <div class="stat-value">{confirmed_count}</div>
            <div class="stat-note">KES {confirmed_count * 500:,} recorded</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Pending Submissions</div>
            <div class="stat-value">{pending_count}</div>
            <div class="stat-note">Review in Payments tab</div>
        </div>
    </div>

    {banner}

    <section>
        <h2>Platform Announcement Banner</h2>
        <form method="post" action="/admin/announcement" class="form-grid">
            <div class="form-field" style="grid-column: 1 / -1;">
                <label for="announcement_text">Notice Shown Across Workspace</label>
                <input type="text" id="announcement_text" name="announcement_text" value="{announcement}" required />
            </div>
            <div>
                <button type="submit" class="btn">Save Announcement</button>
            </div>
        </form>
    </section>

    <section>
        <h2>Add Financial or Taxation Study Note</h2>
        <form method="post" action="/admin/notes/add">
            <div class="form-grid">
                <div class="form-field">
                    <label for="note_topic">Topic Name</label>
                    <input type="text" id="note_topic" name="topic" placeholder="e.g. Capital Allowances" required />
                </div>
                <div class="form-field">
                    <label for="note_category">Category</label>
                    <input type="text" id="note_category" name="category" value="Financial & Taxation Accounts" required />
                </div>
            </div>
            <div class="form-field" style="margin-bottom: 12px;">
                <label for="note_summary">Summary</label>
                <textarea id="note_summary" name="summary" rows="2" required></textarea>
            </div>
            <div class="form-field" style="margin-bottom: 12px;">
                <label for="note_points">Theory &amp; Worked Calculation Points (one per line)</label>
                <textarea id="note_points" name="points_raw" rows="3" placeholder="Theory: ...&#10;Calculation: ..."></textarea>
            </div>
            <div class="form-field" style="margin-bottom: 12px;">
                <label for="note_formula">Key Rule / Formula &amp; Example</label>
                <input type="text" id="note_formula" name="formula_or_rule" placeholder="e.g. Net Tax = Gross Tax - Relief" />
            </div>
            <button type="submit" class="btn">Publish Study Note</button>
        </form>
    </section>

    <section>
        <h2>Add Practice Question</h2>
        <form method="post" action="/admin/questions/add">
            <div class="form-grid">
                <div class="form-field">
                    <label for="q_topic_input">Topic</label>
                    <input type="text" id="q_topic_input" name="topic" placeholder="e.g. VAT & Indirect Taxes" required />
                </div>
                <div class="form-field">
                    <label for="q_answer">Correct Option Letter (A, B, C, or D)</label>
                    <select id="q_answer" name="answer">
                        <option value="A">A</option>
                        <option value="B">B</option>
                        <option value="C">C</option>
                        <option value="D">D</option>
                    </select>
                </div>
            </div>
            <div class="form-field" style="margin-bottom: 12px;">
                <label for="q_text">Question Prompt (Theory or Calculation)</label>
                <input type="text" id="q_text" name="question" required />
            </div>
            <div class="form-grid">
                <div class="form-field">
                    <label for="opt_a">Option A</label>
                    <input type="text" id="opt_a" name="opt_a" placeholder="A. ..." required />
                </div>
                <div class="form-field">
                    <label for="opt_b">Option B</label>
                    <input type="text" id="opt_b" name="opt_b" placeholder="B. ..." required />
                </div>
                <div class="form-field">
                    <label for="opt_c">Option C</label>
                    <input type="text" id="opt_c" name="opt_c" placeholder="C. ..." required />
                </div>
                <div class="form-field">
                    <label for="opt_d">Option D</label>
                    <input type="text" id="opt_d" name="opt_d" placeholder="D. ..." required />
                </div>
            </div>
            <div class="form-field" style="margin-bottom: 12px;">
                <label for="q_exp">Theory or Calculation Explanation</label>
                <input type="text" id="q_exp" name="explanation" required />
            </div>
            <button type="submit" class="btn">Add Question to Bank</button>
        </form>
    </section>

    <section>
        <h2>Accounts &amp; Subscription Access</h2>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Role</th>
                    <th>Subscription</th>
                    <th>Access Control</th>
                </tr>
            </thead>
            <tbody>{user_rows}</tbody>
        </table>
    </section>
    """


@app.get("/", response_class=HTMLResponse)
def login_page(request: Request, msg: str = "", err: str = ""):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/admin" if user["role"] == "admin" else "/student", status_code=303)

    notice = f"<div class='notice-banner'>{msg}</div>" if msg else ""
    error_box = (
        f"<div class='note-formula' style='border-color:#fca5a5;background:#fef2f2;color:#991b1b;margin-bottom:12px;'>{err}</div>"
        if err
        else ""
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Sign In — Financial &amp; Taxation Accounts</title>
        <style>{APP_STYLES}</style>
    </head>
    <body>
        <div class="auth-grid">
            <div class="auth-card">
                <h2 style="margin-top: 0;">Sign In</h2>
                <p style="color: #475569; margin-bottom: 10px;">Financial &amp; Taxation Accounts workspace.</p>
                {notice}
                {error_box}
                <form action="/login" method="post">
                    <label for="login_email">Email</label>
                    <input type="email" id="login_email" name="email" placeholder="{ADMIN_EMAIL}" required />

                    <label for="login_password">Password</label>
                    <input type="password" id="login_password" name="password" placeholder="Enter password" required />

                    <button type="submit" class="btn">Sign In</button>
                </form>
                <div class="owner-box">
                    <strong>Owner Account:</strong><br />
                    Name: {OWNER_NAME} | Phone: {OWNER_PHONE}<br />
                    Email: <code>{ADMIN_EMAIL}</code><br />
                    Student Demo: <code>{STUDENT_EMAIL}</code> / <code>{STUDENT_PASSWORD}</code>
                </div>
            </div>

            <div class="auth-card">
                <h2 style="margin-top: 0;">Create Student Account</h2>
                <p style="color: #475569; margin-bottom: 10px;">Register as a learner to track scores, practice topics, and take the 50-question timed challenge.</p>
                <form action="/register" method="post">
                    <label for="reg_name">Full Name</label>
                    <input type="text" id="reg_name" name="name" placeholder="Your full name" required />

                    <label for="reg_phone">Phone Number</label>
                    <input type="text" id="reg_phone" name="phone" placeholder="07XXXXXXXX or 2547XXXXXXXX" required />

                    <label for="reg_email">Email</label>
                    <input type="email" id="reg_email" name="email" placeholder="student@domain.com" required />

                    <label for="reg_password">Password</label>
                    <input type="password" id="reg_password" name="password" minlength="6" required />

                    <button type="submit" class="btn btn-secondary">Register Student Account</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """


@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    user = verify_login(email, password)
    if not user:
        return RedirectResponse(url="/?err=Invalid+email+or+password", status_code=303)

    target = "/admin" if user["role"] == "admin" else "/student"
    response = RedirectResponse(url=target, status_code=303)
    token = create_session_token(
        {"email": user["email"], "name": user["name"], "role": user["role"]}
    )
    response.set_cookie(key=SESSION_COOKIE_NAME, value=token, httponly=True, samesite="lax")
    return response


@app.post("/register")
def register(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    ok, message = database.create_student_user(
        email=email,
        name=name,
        phone=phone,
        password_hash=pwd_context.hash(password),
    )
    if not ok:
        return RedirectResponse(url=f"/?err={message}", status_code=303)
    return RedirectResponse(url=f"/?msg={message}", status_code=303)


@app.post("/payments/record", response_class=HTMLResponse)
async def record_payment(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    form = await request.form()
    phone = str(form.get("phone", "")).strip()
    reference = str(form.get("reference", "")).strip().upper()
    plan = str(form.get("plan", "30-Day Full Access (KES 500)")).strip()

    database.add_payment(
        reference=reference or "MPX-PENDING",
        user_email=user["email"],
        phone=phone or OWNER_PHONE,
        plan=plan,
        amount="KES 500",
    )

    base_path = "/admin" if user["role"] == "admin" else "/student"
    body = build_payments_section(
        user,
        base_path,
        status_message=f"Payment reference {reference} submitted for {user['email']} (Pay to {OWNER_PHONE}).",
    )
    return render_shell(user, "Payments", "payments", body)


@app.post("/admin/payments/{payment_id}/status", response_class=HTMLResponse)
def admin_payment_status(payment_id: int, request: Request, status: str = Form(...)):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    clean_status = status if status in {"Confirmed", "Rejected", "Submitted"} else "Submitted"
    database.update_payment_status(payment_id, clean_status)
    body = build_payments_section(
        user,
        "/admin",
        status_message=f"Payment #{payment_id} updated to {clean_status}.",
    )
    return render_shell(user, "Payments", "payments", body)


@app.post("/admin/users/subscription", response_class=HTMLResponse)
def admin_user_subscription(
    request: Request,
    email: str = Form(...),
    status: str = Form(...),
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    clean_status = "Active" if status == "Active" else "Pending"
    database.set_user_subscription(email, clean_status)
    body = build_owner_controls_section(
        status_message=f"Subscription for {email} set to {clean_status}."
    )
    return render_shell(user, "Owner Controls", "manage", body)


@app.post("/admin/announcement", response_class=HTMLResponse)
def admin_announcement(request: Request, announcement_text: str = Form(...)):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    database.set_announcement(announcement_text)
    body = build_owner_controls_section(status_message="Platform notice updated.")
    return render_shell(user, "Owner Controls", "manage", body)


@app.post("/admin/notes/add", response_class=HTMLResponse)
def admin_add_note(
    request: Request,
    topic: str = Form(...),
    category: str = Form(...),
    summary: str = Form(...),
    points_raw: str = Form(""),
    formula_or_rule: str = Form(""),
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    points = [line.strip() for line in points_raw.splitlines() if line.strip()]
    database.add_custom_note(
        topic=topic,
        category=category,
        summary=summary,
        points=points,
        formula_or_rule=formula_or_rule,
    )
    body = build_owner_controls_section(status_message=f"Added study note under topic '{topic}'.")
    return render_shell(user, "Owner Controls", "manage", body)


@app.post("/admin/questions/add", response_class=HTMLResponse)
def admin_add_question(
    request: Request,
    topic: str = Form(...),
    question: str = Form(...),
    opt_a: str = Form(...),
    opt_b: str = Form(...),
    opt_c: str = Form(...),
    opt_d: str = Form(...),
    answer: str = Form(...),
    explanation: str = Form(...),
):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/", status_code=303)

    options = [opt_a.strip(), opt_b.strip(), opt_c.strip(), opt_d.strip()]
    database.add_custom_question(
        topic=topic,
        question=question,
        options=options,
        answer=answer,
        explanation=explanation,
    )
    body = build_owner_controls_section(status_message=f"Added question to topic '{topic}'.")
    return render_shell(user, "Owner Controls", "manage", body)


def render_notes_body(user: dict, base_path: str, note_topic: str) -> str:
    notes = get_all_notes()
    note_topic_list = ["All"] + [
        n.get("topic") for n in notes if isinstance(n, dict) and n.get("topic")
    ]
    filtered_notes = filter_by_topic(notes, note_topic)
    n_select_html = build_topic_select(note_topic_list, note_topic, "n_topic", "note_topic")
    notes_html = "".join(format_note(n, base_path) for n in filtered_notes) or "<p>No study notes available.</p>"
    return f"""
    <section>
        <h2>Financial &amp; Taxation Study Notes ({len(filtered_notes)} of {len(notes)} shown)</h2>
        <form method="get" action="{base_path}" class="toolbar">
            <input type="hidden" name="tab" value="notes" />
            <div>
                <label for="n_topic"><strong>Topic:</strong></label>
                {n_select_html}
                <button type="submit" class="btn btn-sm">Filter</button>
            </div>
            <a class="btn btn-secondary btn-sm" href="{base_path}?tab=notes">All Topics</a>
        </form>
        <div>{notes_html}</div>
    </section>
    """


@app.get("/admin", response_class=HTMLResponse)
def admin_home(
    request: Request,
    tab: str = "overview",
    topic: str = "All",
    note_topic: str = "All",
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if user["role"] != "admin":
        return RedirectResponse(url="/student", status_code=303)

    active_tab = tab if tab in {"overview", "notes", "questions", "payments", "manage"} else "overview"

    if active_tab == "overview":
        body_content = build_overview_section(user, "/admin")
    elif active_tab == "notes":
        body_content = render_notes_body(user, "/admin", note_topic)
    elif active_tab == "questions":
        all_questions = get_all_questions()
        counts = topic_counts(all_questions)
        filtered_questions = filter_by_topic(all_questions, topic)
        breakdown_pills = " ".join(
            f"<span class='badge'>{t}: {c}</span>" for t, c in counts.items()
        ) or "<span class='badge'>No questions loaded</span>"
        q_select_html = build_topic_select(["All"] + list(counts.keys()), topic, "q_topic", "topic")
        questions_only_html = (
            "".join(format_tickable_question_admin(q) for q in filtered_questions)
            or "<li class='q-card'>No questions match this topic.</li>"
        )
        answers_only_html = (
            "".join(format_answer_key_item(q) for q in filtered_questions)
            or "<li>No answers available.</li>"
        )
        body_content = f"""
        <section>
            <h2>Question Bank Preview ({len(filtered_questions)} of {len(all_questions)} shown)</h2>
            <div style="margin-bottom: 12px;">{breakdown_pills}</div>
            <form method="get" action="/admin" class="toolbar">
                <input type="hidden" name="tab" value="questions" />
                <div>
                    <label for="q_topic"><strong>Topic:</strong></label>
                    {q_select_html}
                    <button type="submit" class="btn btn-sm">Filter</button>
                </div>
                <a class="btn btn-secondary btn-sm" href="/admin?tab=questions">Show All</a>
            </form>
            <ol style="padding-left: 0; list-style: none;">{questions_only_html}</ol>
        </section>
        <section>
            <h2>Separated Answer Key &amp; Explanations ({len(filtered_questions)} items)</h2>
            <ol>{answers_only_html}</ol>
        </section>
        """
    elif active_tab == "payments":
        body_content = build_payments_section(user, "/admin")
    else:
        body_content = build_owner_controls_section()

    return render_shell(user, "Owner & Admin Workspace", active_tab, body_content)


@app.get("/student", response_class=HTMLResponse)
def student_home(
    request: Request,
    tab: str = "overview",
    topic: str = "All",
    note_topic: str = "All",
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if user["role"] != "student":
        return RedirectResponse(url="/admin", status_code=303)

    active_tab = tab if tab in {"overview", "notes", "questions", "payments"} else "overview"

    if active_tab == "overview":
        body_content = build_overview_section(user, "/student")
    elif active_tab == "notes":
        body_content = render_notes_body(user, "/student", note_topic)
    elif active_tab == "questions":
        all_questions = get_all_questions()
        counts = topic_counts(all_questions)
        filtered_questions = filter_by_topic(all_questions, topic)
        q_select_html = build_topic_select(["All"] + list(counts.keys()), topic, "q_topic", "topic")

        q_cards = []
        for idx, q in enumerate(filtered_questions, start=1):
            if not isinstance(q, dict):
                continue
            qid = q.get("id")
            opts = "".join(
                f"<label class='tick-opt'>"
                f"<input type='radio' name='q_{qid}' value='{opt[:1]}' /> {opt}"
                f"</label>"
                for opt in q.get("options", [])
            )
            q_cards.append(
                f"<div class='q-card'>"
                f"<div class='q-meta'>Question {idx} (#{qid}) • {q.get('topic', '')}</div>"
                f"<div class='q-title'><strong>{q.get('question', '')}</strong></div>"
                f"<div>{opts}</div>"
                f"</div>"
            )

        body_content = f"""
        <section>
            <h2>Practice Questions ({len(filtered_questions)} available)</h2>
            <p>Tick your answer for each question. Results and explanations appear after submission.</p>
            <form method="get" action="/student" class="toolbar">
                <input type="hidden" name="tab" value="questions" />
                <div>
                    <label for="q_topic"><strong>Topic:</strong></label>
                    {q_select_html}
                    <button type="submit" class="btn btn-sm">Load Topic</button>
                </div>
                <a class="btn btn-secondary btn-sm" href="/student?tab=questions&topic=All">All Topics</a>
            </form>
            <form method="post" action="/student/submit">
                <input type="hidden" name="topic" value="{topic}" />
                {"".join(q_cards) or "<p>No questions found for this topic.</p>"}
                <button type="submit" class="btn">Submit Practice Answers</button>
            </form>
        </section>
        """
    else:
        body_content = build_payments_section(user, "/student")

    return render_shell(user, "Student Workspace", active_tab, body_content)


@app.post("/student/submit", response_class=HTMLResponse)
async def submit_quiz(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if user["role"] != "student":
        return RedirectResponse(url="/admin", status_code=303)

    form = await request.form()
    selected_topic = str(form.get("topic", "All"))
    all_questions = get_all_questions()
    target_questions = filter_by_topic(all_questions, selected_topic)

    correct = 0
    review_items = []
    for idx, q in enumerate(target_questions, start=1):
        if not isinstance(q, dict):
            continue
        qid = q.get("id")
        chosen = str(form.get(f"q_{qid}", "")).strip().upper()
        expected = str(q.get("answer", "")).strip().upper()
        is_right = chosen == expected and expected != ""
        if is_right:
            correct += 1
            status_html = "<span class='review-ok'>Correct</span>"
        else:
            status_html = (
                f"<span class='review-bad'>Incorrect</span> "
                f"(Your tick: <strong>{chosen or 'None'}</strong> | Correct: <strong>{expected}</strong>)"
            )
        review_items.append(
            f"<li style='margin-bottom: 14px;'>"
            f"<div><strong>Q{idx} [{q.get('topic', '')}]</strong> {q.get('question', '')}</div>"
            f"<div>{status_html} — <em>{q.get('explanation', '')}</em></div>"
            f"</li>"
        )

    total = len(target_questions)
    pct = (correct / total * 100) if total > 0 else 0.0
    database.log_progress(
        user_email=user["email"],
        mode="Topic Practice",
        detail=selected_topic,
        correct_count=correct,
        total_count=total,
        points_earned=correct,
        max_points=total,
        score_label=f"{correct}/{total} ({pct:.1f}%)",
    )

    body_content = f"""
    <section>
        <h2>Practice Session Summary</h2>
        <p><strong>Score:</strong> {correct} / {total} ({pct:.1f}%) • <strong>Topic:</strong> {selected_topic}</p>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <a class="btn" href="/student?tab=questions&topic={selected_topic}">Practice Again</a>
            <a class="btn btn-secondary" href="/student?tab=overview">View Progress Overview</a>
        </div>
    </section>
    <section>
        <h2>Separated Answers &amp; Explanations</h2>
        <ol>{"".join(review_items)}</ol>
    </section>
    """
    return render_shell(user, "Practice Results", "questions", body_content)


@app.get("/challenge", response_class=HTMLResponse)
def challenge_page(request: Request, block: int = 1):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    questions, current_block, total_blocks = get_challenge_block(block)
    seconds_allowed = CHALLENGE_SECONDS_PER_BLOCK
    max_points = len(questions) * POINTS_PER_CHALLENGE_QUESTION

    block_links = " ".join(
        f"<a class='btn {'btn-sm' if b == current_block else 'btn-secondary btn-sm'}' "
        f"href='/challenge?block={b}'>Block {b} ({(b-1)*50 + 1}–{b*50})</a>"
        for b in range(1, total_blocks + 1)
    )

    cards_html = []
    for idx, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            continue
        qid = q.get("id")
        opts_html = "".join(
            f"<label class='tick-opt'>"
            f"<input type='radio' name='q_{qid}' value='{opt[:1]}' /> {opt}"
            f"</label>"
            for opt in q.get("options", [])
        )
        cards_html.append(
            f"<div class='q-card'>"
            f"<div class='q-meta'>Question {idx} of {len(questions)} • {q.get('topic', '')} • {POINTS_PER_CHALLENGE_QUESTION} Points</div>"
            f"<div class='q-title'><strong>{q.get('question', '')}</strong></div>"
            f"<div>{opts_html}</div>"
            f"</div>"
        )

    body_content = f"""
    <section>
        <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px;">
            <div>
                <h2 style="margin-bottom: 4px;">50-Question Mixed-Topic Challenge</h2>
                <p style="margin: 0; color: #475569;">2 hours 30 minutes • {POINTS_PER_CHALLENGE_QUESTION} points per question ({max_points} points total)</p>
            </div>
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">{block_links}</div>
        </div>
    </section>

    <div class="timer-bar">
        <span><strong>Block {current_block} of {total_blocks}</strong> • Mixed Topics • {max_points} Points Total</span>
        <span class="timer-clock" id="countdown">02:30:00</span>
    </div>

    <form id="challengeForm" method="post" action="/challenge/submit">
        <input type="hidden" name="block" value="{current_block}" />
        {"".join(cards_html) or "<p>No challenge questions available.</p>"}
        <section style="text-align: right;">
            <button type="submit" class="btn">Submit Challenge ({max_points} Points)</button>
        </section>
    </form>

    <script>
        let remaining = {seconds_allowed};
        const display = document.getElementById("countdown");
        const form = document.getElementById("challengeForm");

        function renderTimer() {{
            const hrs = Math.floor(remaining / 3600);
            const mins = Math.floor((remaining % 3600) / 60);
            const secs = remaining % 60;
            display.textContent =
                String(hrs).padStart(2, "0") + ":" +
                String(mins).padStart(2, "0") + ":" +
                String(secs).padStart(2, "0");
        }}

        renderTimer();
        const interval = setInterval(() => {{
            remaining -= 1;
            if (remaining <= 0) {{
                clearInterval(interval);
                display.textContent = "00:00:00";
                form.submit();
                return;
            }}
            renderTimer();
        }}, 1000);
    </script>
    """
    return render_shell(user, f"50-Q Challenge (Block {current_block})", "challenge", body_content)


@app.post("/challenge/submit", response_class=HTMLResponse)
async def submit_challenge(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    form = await request.form()
    block = int(form.get("block", 1) or 1)
    questions, current_block, _ = get_challenge_block(block)

    earned_points = 0
    correct_count = 0
    review_items = []

    for idx, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            continue
        qid = q.get("id")
        chosen = str(form.get(f"q_{qid}", "")).strip().upper()
        expected = str(q.get("answer", "")).strip().upper()
        is_right = chosen == expected and expected != ""

        if is_right:
            correct_count += 1
            earned_points += POINTS_PER_CHALLENGE_QUESTION
            status_html = (
                f"<span class='review-ok'>Correct (+{POINTS_PER_CHALLENGE_QUESTION} / "
                f"{POINTS_PER_CHALLENGE_QUESTION} pts)</span>"
            )
        else:
            status_html = (
                f"<span class='review-bad'>Incorrect (0 / {POINTS_PER_CHALLENGE_QUESTION} pts)</span> "
                f"— Your tick: <strong>{chosen or 'None'}</strong> | Correct: <strong>{expected}</strong>"
            )

        review_items.append(
            f"<li style='margin-bottom: 14px;'>"
            f"<div><strong>Q{idx} [{q.get('topic', '')}]</strong> {q.get('question', '')}</div>"
            f"<div>{status_html} — <em>{q.get('explanation', '')}</em></div>"
            f"</li>"
        )

    max_points = len(questions) * POINTS_PER_CHALLENGE_QUESTION
    percentage = (earned_points / max_points * 100) if max_points > 0 else 0.0
    database.log_progress(
        user_email=user["email"],
        mode="50-Q Challenge",
        detail=f"Block {current_block} ({correct_count}/{len(questions)} right)",
        correct_count=correct_count,
        total_count=len(questions),
        points_earned=earned_points,
        max_points=max_points,
        score_label=f"{earned_points}/{max_points} pts ({percentage:.1f}%)",
    )

    base_path = "/admin" if user["role"] == "admin" else "/student"
    body_content = f"""
    <section>
        <h2>Challenge Results — Block {current_block}</h2>
        <p>
            <strong>Total Score:</strong> {earned_points} / {max_points} points ({percentage:.1f}%) •
            <strong>Correct:</strong> {correct_count} / {len(questions)} ({POINTS_PER_CHALLENGE_QUESTION} pts each)
        </p>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <a class="btn" href="/challenge?block={current_block}">Retry Block {current_block}</a>
            <a class="btn btn-secondary" href="{base_path}?tab=overview">Back to Overview</a>
        </div>
    </section>
    <section>
        <h2>Separated Answers &amp; Explanations</h2>
        <ol>{"".join(review_items)}</ol>
    </section>
    """
    return render_shell(user, "Challenge Results", "challenge", body_content)


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return response
    