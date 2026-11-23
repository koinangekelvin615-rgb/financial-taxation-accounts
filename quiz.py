from __future__ import annotations

BASE_TOPICS = [
    "Financial Statements",
    "PAYE & Income Tax",
    "VAT & Indirect Taxes",
    "Turnover Tax",
    "Withholding Tax",
    "Capital Gains Tax",
]

SEED_QUESTIONS: list[dict] = [
    # --- Financial Statements (Theory + Calculations) ---
    {
        "id": 1,
        "topic": "Financial Statements",
        "question": "Which statement reports a business's assets, liabilities, and equity at a specific date?",
        "options": [
            "A. Statement of Financial Position",
            "B. Statement of Profit or Loss",
            "C. Trial Balance",
            "D. Cash Receipts Journal",
        ],
        "answer": "A",
        "explanation": "Theory: The Statement of Financial Position shows assets, liabilities, and capital/equity as at a specific reporting date.",
    },
    {
        "id": 2,
        "topic": "Financial Statements",
        "question": "A trader has sales of KES 480,000, opening stock of KES 60,000, purchases of KES 230,000, and closing stock of KES 50,000. What is gross profit?",
        "options": [
            "A. KES 240,000",
            "B. KES 250,000",
            "C. KES 230,000",
            "D. KES 260,000",
        ],
        "answer": "A",
        "explanation": "Calculation: Cost of sales = 60,000 + 230,000 - 50,000 = KES 240,000. Gross profit = 480,000 - 240,000 = KES 240,000.",
    },
    {
        "id": 3,
        "topic": "Financial Statements",
        "question": "If current assets are KES 270,000 and current liabilities are KES 150,000, what is the current ratio?",
        "options": [
            "A. 1.80",
            "B. 0.56",
            "C. 1.20",
            "D. 2.20",
        ],
        "answer": "A",
        "explanation": "Calculation: Current ratio = Current assets / Current liabilities = 270,000 / 150,000 = 1.80.",
    },
    {
        "id": 4,
        "topic": "Financial Statements",
        "question": "Under the accruals basis of accounting, when are expenses recognized in the Statement of Profit or Loss?",
        "options": [
            "A. In the period incurred, regardless of when cash is paid",
            "B. Only when cash leaves the bank account",
            "C. Only when annual financial statements are audited",
            "D. When the supplier issues a proforma quote",
        ],
        "answer": "A",
        "explanation": "Theory: Accruals accounting recognizes expenses in the period they are incurred rather than strictly when cash is paid.",
    },
    # --- PAYE & Income Tax (Theory + Calculations) ---
    {
        "id": 5,
        "topic": "PAYE & Income Tax",
        "question": "How is net PAYE tax payable determined after computing gross tax on taxable employment income?",
        "options": [
            "A. Gross tax less allowable reliefs (such as personal and insurance relief)",
            "B. Gross tax plus personal relief",
            "C. Gross pay multiplied by 16%",
            "D. Net pay less gross tax",
        ],
        "answer": "A",
        "explanation": "Theory: Allowable reliefs (such as personal relief of KES 2,400/month and qualifying insurance relief) are subtracted from gross tax to get net PAYE.",
    },
    {
        "id": 6,
        "topic": "PAYE & Income Tax",
        "question": "An employee has gross tax of KES 46,800, personal relief of KES 2,400, and allowable insurance relief of KES 1,200. What is net PAYE payable?",
        "options": [
            "A. KES 43,200",
            "B. KES 44,400",
            "C. KES 45,600",
            "D. KES 50,400",
        ],
        "answer": "A",
        "explanation": "Calculation: Net PAYE = 46,800 - (2,400 + 1,200) = 46,800 - 3,600 = KES 43,200.",
    },
    {
        "id": 7,
        "topic": "PAYE & Income Tax",
        "question": "If gross salary is KES 120,000 and allowable pre-tax deductions total KES 14,500, what is taxable employment income?",
        "options": [
            "A. KES 105,500",
            "B. KES 134,500",
            "C. KES 120,000",
            "D. KES 95,500",
        ],
        "answer": "A",
        "explanation": "Calculation: Taxable income = Gross salary - Allowable deductions = 120,000 - 14,500 = KES 105,500.",
    },
    # --- VAT & Indirect Taxes (Theory + Calculations) ---
    {
        "id": 8,
        "topic": "VAT & Indirect Taxes",
        "question": "What is the key accounting difference between zero-rated supplies and exempt supplies under VAT?",
        "options": [
            "A. Zero-rated supplies are taxed at 0% with input VAT recovery; exempt supplies carry no output VAT and disallow input VAT recovery",
            "B. Exempt supplies allow full input VAT refunds while zero-rated supplies ban input VAT claims",
            "C. Both zero-rated and exempt supplies are taxed at 16%",
            "D. Exempt supplies apply only to imports",
        ],
        "answer": "A",
        "explanation": "Theory: Zero-rated supplies carry a 0% output rate while preserving input VAT deduction rights; exempt supplies carry no output VAT and do not permit input VAT deduction on related costs.",
    },
    {
        "id": 9,
        "topic": "VAT & Indirect Taxes",
        "question": "A VAT-registered business has output VAT of KES 176,000 and allowable input VAT of KES 112,500 in a tax period. What is net VAT payable?",
        "options": [
            "A. KES 63,500",
            "B. KES 288,500",
            "C. KES 112,500",
            "D. KES 53,500",
        ],
        "answer": "A",
        "explanation": "Calculation: Net VAT payable = Output VAT - Input VAT = 176,000 - 112,500 = KES 63,500.",
    },
    {
        "id": 10,
        "topic": "VAT & Indirect Taxes",
        "question": "A taxable supply has a VAT-exclusive price of KES 250,000 at the standard 16% VAT rate. What is the output VAT charged?",
        "options": [
            "A. KES 40,000",
            "B. KES 290,000",
            "C. KES 34,483",
            "D. KES 210,000",
        ],
        "answer": "A",
        "explanation": "Calculation: Output VAT = 16% x KES 250,000 = KES 40,000 (giving a VAT-inclusive price of KES 290,000).",
    },
    # --- Turnover Tax (Theory + Calculations) ---
    {
        "id": 11,
        "topic": "Turnover Tax",
        "question": "How is Turnover Tax (TOT) calculated for a qualifying business?",
        "options": [
            "A. As a percentage of gross turnover/sales without deducting business expenses",
            "B. As a percentage of net profit after deducting depreciation",
            "C. Only on unsold closing stock",
            "D. As a fixed fee regardless of sales",
        ],
        "answer": "A",
        "explanation": "Theory: Turnover tax is assessed on gross sales/turnover and does not allow expense deductions.",
    },
    {
        "id": 12,
        "topic": "Turnover Tax",
        "question": "A qualifying small business records gross turnover of KES 800,000 in a month. At the 1.5% turnover tax rate, what is the TOT payable?",
        "options": [
            "A. KES 12,000",
            "B. KES 8,000",
            "C. KES 120,000",
            "D. KES 15,000",
        ],
        "answer": "A",
        "explanation": "Calculation: Turnover tax = 1.5% x KES 800,000 = KES 12,000.",
    },
    {
        "id": 13,
        "topic": "Turnover Tax",
        "question": "A business under the 1.5% turnover tax regime has gross sales of KES 1,400,000 and operating expenses of KES 950,000. What is the turnover tax due?",
        "options": [
            "A. KES 21,000",
            "B. KES 6,750",
            "C. KES 14,250",
            "D. KES 14,000",
        ],
        "answer": "A",
        "explanation": "Calculation: TOT applies to gross sales, not net profit: 1.5% x KES 1,400,000 = KES 21,000.",
    },
    # --- Withholding Tax (Theory + Calculations) ---
    {
        "id": 14,
        "topic": "Withholding Tax",
        "question": "What is Withholding Tax (WHT) in taxation accounting?",
        "options": [
            "A. Tax deducted at source by the payer from a qualifying payment and remitted to the tax authority",
            "B. A property tax paid only when buying land",
            "C. A refund paid by the taxpayer to suppliers",
            "D. A penalty charged for late bookkeeping",
        ],
        "answer": "A",
        "explanation": "Theory: Withholding tax is collected at source by a payer/withholding agent on specified payments and remitted to the revenue authority.",
    },
    {
        "id": 15,
        "topic": "Withholding Tax",
        "question": "A company pays a resident consultant a gross fee of KES 200,000 subject to 5% withholding tax. How much WHT is withheld and what is the net amount paid?",
        "options": [
            "A. WHT = KES 10,000; Net paid = KES 190,000",
            "B. WHT = KES 20,000; Net paid = KES 180,000",
            "C. WHT = KES 6,000; Net paid = KES 194,000",
            "D. WHT = KES 10,000; Net paid = KES 210,000",
        ],
        "answer": "A",
        "explanation": "Calculation: WHT = 5% x 200,000 = KES 10,000. Net payment = 200,000 - 10,000 = KES 190,000.",
    },
    {
        "id": 16,
        "topic": "Withholding Tax",
        "question": "A resident contractor bills KES 350,000 for contractual services subject to 3% withholding tax. What is the withholding tax deducted?",
        "options": [
            "A. KES 10,500",
            "B. KES 17,500",
            "C. KES 3,500",
            "D. KES 52,500",
        ],
        "answer": "A",
        "explanation": "Calculation: WHT = 3% x KES 350,000 = KES 10,500 (net payout = KES 339,500).",
    },
    # --- Capital Gains Tax (Theory + Calculations) ---
    {
        "id": 17,
        "topic": "Capital Gains Tax",
        "question": "On which amount is Capital Gains Tax (CGT) calculated when a chargeable asset is transferred?",
        "options": [
            "A. Net realized gain (transfer value less allowable costs and incidental expenses)",
            "B. Gross selling price before deducting acquisition cost",
            "C. Opening bank balance of the seller",
            "D. Annual rental income from the property",
        ],
        "answer": "A",
        "explanation": "Theory: CGT is charged on the net capital gain after deducting acquisition cost, allowable enhancement costs, and incidental transfer/acquisition costs.",
    },
    {
        "id": 18,
        "topic": "Capital Gains Tax",
        "question": "Land is bought for KES 5,000,000 with KES 500,000 in allowable improvements/costs and sold for KES 8,000,000. At a 15% CGT rate, what is the CGT payable?",
        "options": [
            "A. KES 375,000",
            "B. KES 1,200,000",
            "C. KES 450,000",
            "D. KES 250,000",
        ],
        "answer": "A",
        "explanation": "Calculation: Net gain = 8,000,000 - (5,000,000 + 500,000) = KES 2,500,000. CGT (15%) = 0.15 x 2,500,000 = KES 375,000.",
    },
    {
        "id": 19,
        "topic": "Capital Gains Tax",
        "question": "An asset is sold for KES 3,200,000 after being acquired for KES 2,100,000 with KES 100,000 incidental costs. At 15% CGT, what is the CGT due?",
        "options": [
            "A. KES 150,000",
            "B. KES 165,000",
            "C. KES 480,000",
            "D. KES 180,000",
        ],
        "answer": "A",
        "explanation": "Calculation: Net gain = 3,200,000 - (2,100,000 + 100,000) = KES 1,000,000. CGT (15%) = 0.15 x 1,000,000 = KES 150,000.",
    },
]


def _build_challenge_bank(base_qs: list[dict], count: int = 50) -> list[dict]:
    items: list[dict] = []
    qid = 101
    idx = 0
    while len(items) < count:
        src = base_qs[idx % len(base_qs)]
        cycle = (idx // len(base_qs)) + 1
        tag = "" if cycle == 1 else f" [Set {cycle}]"
        items.append(
            {
                "id": qid,
                "topic": src["topic"],
                "question": f"{src['question']}{tag}",
                "options": list(src["options"]),
                "answer": src["answer"],
                "explanation": src["explanation"],
            }
        )
        qid += 1
        idx += 1
    return items


QUESTIONS: list[dict] = list(SEED_QUESTIONS)
CHALLENGE_QUESTIONS: list[dict] = _build_challenge_bank(SEED_QUESTIONS, count=50)


def get_questions() -> list[dict]:
    return QUESTIONS


def get_challenge_questions() -> list[dict]:
    return CHALLENGE_QUESTIONS