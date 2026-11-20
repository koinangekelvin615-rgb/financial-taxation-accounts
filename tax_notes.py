from quiz import TOPIC_LABELS

STUDY_NOTES: list[dict] = [
    {
        "id": 1,
        "topic_slug": "paye",
        "title": "PAYE Basics, Allowable Deductions & Personal Relief",
        "tax_year": "2026",
        "summary": "How employment income is adjusted before applying PAYE tax bands and personal relief.",
        "key_points": [
            "Allowable NSSF contributions are deducted before calculating tax on employment income.",
            "Gross tax from PAYE bands is reduced by monthly personal relief (KES 2,400 standard) and any qualifying reliefs.",
            "PAYE returns and payments are due on or before the 9th day of the following month.",
        ],
    },
    {
        "id": 2,
        "topic_slug": "vat",
        "title": "Output VAT, Input VAT & Monthly Filing Deadlines",
        "tax_year": "2026",
        "summary": "Calculating net VAT payable and distinguishing standard-rated, zero-rated, and exempt supplies.",
        "key_points": [
            "Standard VAT rate on taxable supplies is 16%.",
            "Net VAT payable = Output VAT charged on sales minus allowable Input VAT on taxable purchases.",
            "Zero-rated supplies (0%) differ from exempt supplies in how input VAT is treated.",
            "Monthly VAT returns and payments are due on or before the 20th day of the following month.",
        ],
    },
    {
        "id": 3,
        "topic_slug": "turnover-tax",
        "title": "Turnover Tax (TOT) on Gross Business Sales",
        "tax_year": "2026",
        "summary": "Simplified tax rules for qualifying small businesses based on gross receipts.",
        "key_points": [
            "Turnover Tax is assessed on gross turnover/sales rather than net accounting profit.",
            "Input VAT credits are not claimed against Turnover Tax.",
            "Monthly TOT returns and payments are due on or before the 20th day of the following month.",
        ],
    },
    {
        "id": 4,
        "topic_slug": "withholding-tax",
        "title": "Withholding Tax (WHT) Deduction & Recordkeeping",
        "tax_year": "2026",
        "summary": "Deducting tax at source on qualifying payments and keeping proper supporting records.",
        "key_points": [
            "Withholding tax is collected at source when paying qualifying amounts and remitted to the revenue authority.",
            "Keep withholding tax certificates and payment records to reconcile tax deducted.",
            "Accurate rate application prevents under-withholding penalties and interest.",
        ],
    },
    {
        "id": 5,
        "topic_slug": "rental-income",
        "title": "Residential Rental Income Tax Overview",
        "tax_year": "2026",
        "summary": "How monthly residential rental income is tracked and filed on iTax.",
        "key_points": [
            "Monthly residential rental income tax under the simplified regime is based on gross rent received.",
            "Returns and payments are due on or before the 20th day of the following month.",
            "Use iTax to file returns and generate payment slips accurately.",
        ],
    },
    {
        "id": 6,
        "topic_slug": "tax-procedures",
        "title": "Filing Deadlines, Penalties, Interest & Audit Records",
        "tax_year": "2026",
        "summary": "Core compliance habits for avoiding late penalties and supporting tax returns.",
        "key_points": [
            "Late filing or late payment after statutory deadlines can trigger penalties and/or interest.",
            "Maintain complete invoices, receipts, and ledgers to substantiate figures on returns.",
            "Verify current statutory rules and KRA guidance before classifying unusual transactions.",
        ],
    },
]


def get_notes(topic: str = "all", query: str = "") -> list[dict]:
    clean_topic = (topic or "all").strip().lower()
    clean_query = (query or "").strip().lower()

    results: list[dict] = []
    for note in STUDY_NOTES:
        if clean_topic != "all" and note["topic_slug"] != clean_topic:
            continue
        haystack = " ".join(
            [
                note["title"],
                note["summary"],
                note["topic_slug"],
                TOPIC_LABELS.get(note["topic_slug"], ""),
                " ".join(note["key_points"]),
            ]
        ).lower()
        if clean_query and clean_query not in haystack:
            continue

        item = dict(note)
        item["topic_name"] = TOPIC_LABELS.get(item["topic_slug"], item["topic_slug"].upper())
        results.append(item)
    return results
