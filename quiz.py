import sqlite3
from datetime import datetime

DB_PATH = "taxclass.db"

TOPIC_LABELS = {
    "paye": "PAYE",
    "vat": "Value Added Tax (VAT)",
    "turnover-tax": "Turnover Tax (TOT)",
    "withholding-tax": "Withholding Tax (WHT)",
    "rental-income": "Residential Rental Income Tax",
    "tax-procedures": "Tax Procedures & Deadlines",
}

SEED_QUESTIONS = [
    # PAYE (4)
    (
        "paye",
        "What is the standard monthly personal relief for an employee under Kenyan PAYE rules?",
        "KES 1,408",
        "KES 2,400",
        "KES 3,500",
        "KES 5,000",
        "B",
        "Standard monthly personal relief in Kenya is KES 2,400 (KES 28,800 annually).",
    ),
    (
        "paye",
        "By which day of the following month are PAYE deductions and returns due to KRA?",
        "5th day",
        "9th day",
        "20th day",
        "25th day",
        "B",
        "PAYE returns and payments are due on or before the 9th day of the following month.",
    ),
    (
        "paye",
        "Which deduction is subtracted from gross pay to determine taxable employment income before applying tax bands?",
        "Personal relief",
        "Allowable NSSF contributions",
        "Turnover Tax",
        "Advance tax",
        "B",
        "Allowable NSSF contributions reduce taxable employment income before tax bands and reliefs are applied.",
    ),
    (
        "paye",
        "An employee's gross tax from PAYE bands is KES 18,400 and personal relief is KES 2,400 (no other reliefs). What is net PAYE payable?",
        "KES 20,800",
        "KES 18,400",
        "KES 16,000",
        "KES 14,000",
        "C",
        "Net PAYE = Gross tax (KES 18,400) minus personal relief (KES 2,400) = KES 16,000.",
    ),
    # VAT (4)
    (
        "vat",
        "What is the standard VAT rate in Kenya on taxable supplies?",
        "12%",
        "14%",
        "16%",
        "18%",
        "C",
        "Kenya's standard Value Added Tax rate on taxable goods and services is 16%.",
    ),
    (
        "vat",
        "A VAT-registered trader charges KES 95,000 output VAT and has KES 60,000 allowable input VAT in a period. What is the net VAT payable?",
        "KES 155,000",
        "KES 35,000",
        "KES 60,000",
        "KES 95,000",
        "B",
        "Net VAT payable = Output VAT (KES 95,000) minus allowable Input VAT (KES 60,000) = KES 35,000.",
    ),
    (
        "vat",
        "By what day of the following month are monthly VAT returns and payments due?",
        "9th day",
        "15th day",
        "20th day",
        "28th day",
        "C",
        "Monthly VAT returns and payments are due on or before the 20th day of the following month.",
    ),
    (
        "vat",
        "What is the key difference between zero-rated (0%) supplies and exempt supplies in VAT?",
        "Zero-rated allows input VAT deduction; exempt generally does not",
        "Exempt allows input VAT refund; zero-rated does not",
        "Both carry 16% output VAT",
        "Exempt applies only to exports",
        "A",
        "Zero-rated supplies are taxable at 0% (input VAT can generally be claimed), whereas exempt supplies are outside the charge to VAT and input VAT is not deductible.",
    ),
    # Turnover Tax (4)
    (
        "turnover-tax",
        "Turnover Tax (TOT) in Kenya is assessed on which base?",
        "Net accounting profit",
        "Gross sales / turnover",
        "Imported CIF value",
        "Staff payroll total",
        "B",
        "Turnover Tax is a simplified tax levied on gross business turnover/sales for qualifying small businesses.",
    ),
    (
        "turnover-tax",
        "By what day of the following month are monthly Turnover Tax returns and payments due?",
        "5th day",
        "10th day",
        "20th day",
        "30th day",
        "C",
        "Monthly Turnover Tax returns and payments are due on or before the 20th day of the following month.",
    ),
    (
        "turnover-tax",
        "Can a business registered for Turnover Tax claim input VAT credits against TOT payable?",
        "Yes, on all stock purchases",
        "No, TOT is assessed on gross turnover without input VAT deductions",
        "Yes, if turnover exceeds KES 1 million",
        "Only on equipment",
        "B",
        "Turnover Tax is calculated directly on gross turnover and does not use a VAT input/output credit mechanism.",
    ),
    (
        "turnover-tax",
        "A small trader has KES 400,000 in gross sales in a month under TOT. If TOT is charged on gross sales, what must be tracked first?",
        "Monthly gross sales/receipts",
        "Depreciation schedule",
        "Customs valuation form",
        "Dividends declared",
        "A",
        "Accurate monthly gross sales records determine the TOT base and monthly filing obligation.",
    ),
    # Withholding Tax (4)
    (
        "withholding-tax",
        "What is withholding tax in general tax practice?",
        "Tax collected at source by the payer when making certain payments",
        "A penalty for late filing",
        "A customs duty on imports only",
        "An annual property tax",
        "A",
        "Withholding tax is deducted at source by the person paying qualifying income and remitted to the revenue authority.",
    ),
    (
        "withholding-tax",
        "When a payer withholds tax on a qualifying payment, what document/record supports the tax deducted?",
        "A withholding tax certificate/remittance record",
        "A bill of lading",
        "A payslip only",
        "A land title deed",
        "A",
        "A withholding tax certificate evidences the tax deducted at source so it can be accounted for or credited where applicable.",
    ),
    (
        "withholding-tax",
        "Why does a revenue authority use withholding tax on certain payments?",
        "To collect tax early at the point of payment and improve compliance",
        "To replace all income tax returns permanently",
        "To charge double VAT",
        "To eliminate bookkeeping",
        "A",
        "Withholding tax collects revenue earlier in the cash flow cycle and creates a clear audit trail.",
    ),
    (
        "withholding-tax",
        "If a payment of KES 100,000 is subject to a 5% withholding tax, what amount is withheld?",
        "KES 500",
        "KES 5,000",
        "KES 10,000",
        "KES 95,000",
        "B",
        "5% of KES 100,000 = KES 5,000 withheld.",
    ),
    # Rental Income Tax (4)
    (
        "rental-income",
        "Monthly Rental Income Tax for residential landlords in Kenya is based on which amount?",
        "Gross rental income received",
        "Estimated market value of the plot",
        "Net profit after mortgage interest",
        "Annual council rates",
        "A",
        "Residential rental income tax under the simplified regime is assessed on gross rent received.",
    ),
    (
        "rental-income",
        "When is the monthly residential rental income return and tax due after the month of receipt?",
        "On or before the 20th day of the following month",
        "On the last day of December",
        "Within 90 days of the year-end",
        "On the 1st day of the same month",
        "A",
        "Monthly rental income returns and payments are due on or before the 20th day of the following month.",
    ),
    (
        "rental-income",
        "Under the simplified residential rental income tax regime, are expense deductions like repairs or caretaker wages allowed?",
        "No, it is a flat rate on gross rent received",
        "Yes, all expenses are deducted before applying the rate",
        "Yes, up to 80% of gross rent",
        "Only agent commissions are deducted",
        "A",
        "Because the simplified residential rental tax uses a low rate on gross rent, expense deductions are not subtracted under that regime.",
    ),
    (
        "rental-income",
        "Which platform is used in Kenya to file tax returns and generate payment slips?",
        "iTax",
        "eCitizen birth portal",
        "NHIF employer portal only",
        "NTSA TIMS only",
        "A",
        "iTax is the Kenya Revenue Authority's online portal for tax registration, filing returns, and generating payment slips.",
    ),
    # Tax Procedures & Deadlines (4)
    (
        "tax-procedures",
        "What happens when a taxpayer files a return or pays tax after the statutory deadline?",
        "Late filing penalties and/or late payment interest may apply",
        "The tax liability is automatically cancelled",
        "The deadline moves by one year automatically",
        "No consequences ever apply",
        "A",
        "Missing statutory filing or payment deadlines typically triggers late penalties and/or interest under tax procedure rules.",
    ),
    (
        "tax-procedures",
        "Why is keeping organized records and receipts essential for tax compliance?",
        "To substantiate figures reported on returns during verification or audit",
        "Only for bank loan applications",
        "Records are not needed once a return is filed",
        "Only for importing cars",
        "A",
        "Proper records support declared income, deductions, and credits if KRA reviews or audits a return.",
    ),
    (
        "tax-procedures",
        "Which due date rule applies to BOTH monthly VAT and monthly Turnover Tax in Kenya?",
        "20th day of the following month",
        "9th day of the following month",
        "15th day of the current month",
        "31st March every year",
        "A",
        "Both monthly VAT and monthly Turnover Tax returns and payments fall due on or before the 20th day of the following month.",
    ),
    (
        "tax-procedures",
        "What should a student/taxpayer do if they are unsure whether a specific transaction is exempt or standard-rated?",
        "Check current KRA guidance/legislation rather than guessing",
        "Always treat it as exempt",
        "Skip declaring the transaction",
        "Charge 50% tax",
        "A",
        "Always verify current statutory rules and KRA guidance to avoid under-declaring or over-charging tax.",
    ),
]


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_quiz_db() -> None:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_slug TEXT NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_option TEXT NOT NULL,
                explanation TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_email TEXT NOT NULL,
                mode TEXT NOT NULL,
                topic_slug TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                taken_at TEXT NOT NULL
            )
            """
        )
        count = cursor.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if count == 0:
            cursor.executemany(
                """
                INSERT INTO questions (
                    topic_slug,
                    question_text,
                    option_a,
                    option_b,
                    option_c,
                    option_d,
                    correct_option,
                    explanation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                SEED_QUESTIONS,
            )
        conn.commit()
    finally:
        conn.close()


def get_questions(topic: str = "all") -> list[dict]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        clean_topic = (topic or "all").strip().lower()
        if clean_topic == "all":
            rows = cursor.execute("SELECT * FROM questions ORDER BY id ASC").fetchall()
        else:
            rows = cursor.execute(
                "SELECT * FROM questions WHERE topic_slug = ? ORDER BY id ASC",
                (clean_topic,),
            ).fetchall()

        results: list[dict] = []
        for row in rows:
            item = dict(row)
            item["topic_name"] = TOPIC_LABELS.get(item["topic_slug"], item["topic_slug"].upper())
            results.append(item)
        return results
    finally:
        conn.close()


def save_attempt(
    student_email: str,
    mode: str,
    topic_slug: str,
    score: int,
    total: int,
) -> None:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO quiz_attempts (student_email, mode, topic_slug, score, total, taken_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                student_email.strip().lower(),
                mode.strip().lower(),
                topic_slug.strip().lower(),
                int(score),
                int(total),
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_student_attempts(student_email: str) -> list[dict]:
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT mode, topic_slug, score, total, taken_at
            FROM quiz_attempts
            WHERE student_email = ?
            ORDER BY id DESC
            """,
            (student_email.strip().lower(),),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()