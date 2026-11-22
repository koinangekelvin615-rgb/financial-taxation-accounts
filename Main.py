from html import escape
import importlib

from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="TaxClass Kenya")

# ---------------------------------------------------------------------------
# Optional / Safe Module Wiring
# Checks your sibling modules without crashing if a router name differs.
# ---------------------------------------------------------------------------
MODULE_NAMES = [
    "database",
    "security",
    "student",
    "admin",
    "payment",
    "tax_notes",
    "quiz",
]

loaded_modules = {}
for mod_name in MODULE_NAMES:
    try:
        mod = importlib.import_module(mod_name)
        loaded_modules[mod_name] = mod
        router = getattr(mod, "router", None)
        if router is not None:
            app.include_router(router)
    except Exception as exc:
        print(f"[startup] Module '{mod_name}' skipped/info: {exc}")


# ---------------------------------------------------------------------------
# Job Network Data & Routes (/jobs)
# ---------------------------------------------------------------------------
JOB_POSTINGS = [
    {
        "role": "Tax Associate",
        "company": "Rift Valley Advisory",
        "location": "Nanyuki",
        "job_type": "Full-Time",
        "contact": "careers@riftvalleyadvisory.co.ke",
        "details": "Assist with PAYE, VAT, withholding tax filings, and client tax reconciliations.",
    },
    {
        "role": "Junior Accountant",
        "company": "Nairobi Ledger Ltd",
        "location": "Nairobi",
        "job_type": "Full-Time",
        "contact": "hr@nairobiledger.co.ke",
        "details": "Prepare monthly trial balances, ledger entries, and financial statement schedules.",
    },
    {
        "role": "Audit & Tax Attachment",
        "company": "Mount Kenya Assurance",
        "location": "Nyeri / Remote",
        "job_type": "Attachment / Internship",
        "contact": "attachments@mtkenyaassurance.co.ke",
        "details": "Ideal for accounting and CPA/KASNEB students seeking practical audit and tax exposure.",
    },
]


@app.get("/jobs", response_class=HTMLResponse)
def jobs_page(q: str = Query(default=""), job_type: str = Query(default="")):
    search_term = q.strip().lower()
    selected_type = job_type.strip()

    filtered_jobs = []
    for job in JOB_POSTINGS:
        matches_query = (
            not search_term
            or search_term in job["role"].lower()
            or search_term in job["company"].lower()
            or search_term in job["location"].lower()
            or search_term in job["details"].lower()
        )
        matches_type = not selected_type or selected_type == "All" or job["job_type"] == selected_type
        if matches_query and matches_type:
            filtered_jobs.append(job)

    cards_html = ""
    for job in filtered_jobs:
        cards_html += f"""
        <div class="job-card">
            <h3>{escape(job['role'])}</h3>
            <p><strong>Company:</strong> {escape(job['company'])} &nbsp;|&nbsp;
               <strong>Location:</strong> {escape(job['location'])} &nbsp;|&nbsp;
               <strong>Type:</strong> {escape(job['job_type'])}</p>
            <p>{escape(job['details'])}</p>
            <p><strong>Apply / Contact:</strong> {escape(job['contact'])}</p>
        </div>
        """

    if not cards_html:
        cards_html = "<p>No matching roles found. Try clearing your search or post a new role above.</p>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>TaxClass Kenya — Job Network</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 860px; margin: 32px auto; padding: 0 16px; }}
            .box {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 24px; }}
            .job-card {{ border: 1px solid #ccc; border-radius: 8px; padding: 14px; margin-bottom: 14px; }}
            .row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px; }}
            input, select, textarea, button {{ padding: 8px 10px; font-size: 14px; }}
            input, select {{ flex: 1 1 180px; }}
            textarea {{ width: 100%; box-sizing: border-box; min-height: 70px; margin-bottom: 10px; }}
            button {{ cursor: pointer; }}
        </style>
    </head>
    <body>
        <h1>TaxClass Kenya Job Network</h1>
        <p><a href="/docs">View API Docs (/docs)</a></p>

        <div class="box">
            <h2>Post an Accounting or Tax Opportunity</h2>
            <form action="/jobs" method="post">
                <div class="row">
                    <input name="role" placeholder="Role (e.g., Tax Trainee)" required />
                    <input name="company" placeholder="Company / Firm Name" required />
                    <input name="location" placeholder="Location (e.g., Nairobi, Nanyuki)" required />
                    <select name="job_type">
                        <option value="Full-Time">Full-Time</option>
                        <option value="Part-Time">Part-Time</option>
                        <option value="Contract">Contract</option>
                        <option value="Attachment / Internship">Attachment / Internship</option>
                    </select>
                </div>
                <div class="row">
                    <input name="contact" placeholder="Application email, phone, or link" required />
                </div>
                <textarea name="details" placeholder="Key duties, tax/accounting focus, or requirements..."></textarea>
                <button type="submit">Post Job</button>
            </form>
        </div>

        <div class="box">
            <h2>Filter Open Roles</h2>
            <form action="/jobs" method="get" class="row">
                <input name="q" value="{escape(q)}" placeholder="Search role, company, location, or tax area..." />
                <select name="job_type">
                    <option value="All" {"selected" if selected_type in ("", "All") else ""}>All Types</option>
                    <option value="Full-Time" {"selected" if selected_type == "Full-Time" else ""}>Full-Time</option>
                    <option value="Part-Time" {"selected" if selected_type == "Part-Time" else ""}>Part-Time</option>
                    <option value="Contract" {"selected" if selected_type == "Contract" else ""}>Contract</option>
                    <option value="Attachment / Internship" {"selected" if selected_type == "Attachment / Internship" else ""}>Attachment / Internship</option>
                </select>
                <button type="submit">Filter</button>
            </form>
        </div>

        <h2>Available Roles ({len(filtered_jobs)})</h2>
        {cards_html}
    </body>
    </html>
    """


@app.post("/jobs")
def create_job(
    role: str = Form(...),
    company: str = Form(...),
    location: str = Form(...),
    job_type: str = Form(default="Full-Time"),
    contact: str = Form(...),
    details: str = Form(default=""),
):
    JOB_POSTINGS.insert(
        0,
        {
            "role": role.strip(),
            "company": company.strip(),
            "location": location.strip(),
            "job_type": job_type.strip() or "Full-Time",
            "contact": contact.strip(),
            "details": details.strip() or "Contact employer for full role details.",
        },
    )
    return RedirectResponse(url="/jobs", status_code=303)