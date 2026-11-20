from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from database import has_active_plan

router = APIRouter(prefix="/tax-notes", tags=["Tax Notes"])

TAX_NOTES: List[Dict] = [
    {
        "id": "paye-basics",
        "title": "Pay As You Earn (PAYE) Overview",
        "category": "Income Tax",
        "is_premium": False,
        "summary": "How employers deduct income tax from employee emoluments and remit it to KRA.",
        "key_points": [
            "Applies to employment income including salaries, wages, and taxable benefits.",
            "Personal relief is deducted from gross tax liability before arriving at net PAYE.",
            "Statutory deductions such as NSSF and Affordable Housing Levy follow specific rules.",
            "Employers file and pay PAYE monthly via iTax by the 9th of the following month.",
        ],
    },
    {
        "id": "vat-kenya",
        "title": "Value Added Tax (VAT) Essentials",
        "category": "Indirect Tax",
        "is_premium": True,
        "summary": "Input vs. output VAT, taxable supplies, zero-rated vs. exempt supplies, and monthly filing.",
        "key_points": [
            "Output VAT is charged on taxable supplies; input VAT is tax incurred on eligible business purchases.",
            "Zero-rated supplies are taxed at 0% (allowing input tax deduction), while exempt supplies do not.",
            "VAT returns are typically due by the 20th day of the following month on iTax.",
            "Accurate ETIMS / tax invoice records are essential for claiming input tax.",
        ],
    },
    {
        "id": "turnover-tax",
        "title": "Turnover Tax (TOT) for Small Businesses",
        "category": "SME Tax",
        "is_premium": True,
        "summary": "Simplified gross-receipts taxation for qualifying small businesses within statutory thresholds.",
        "key_points": [
            "Assessed on gross business sales/receipts rather than net profit.",
            "Designed to simplify compliance for eligible micro and small enterprises.",
            "Certain income streams (such as rental income, management/professional fees, and exempt businesses) have separate rules.",
        ],
    },
    {
        "id": "withholding-tax",
        "title": "Withholding Tax (WHT) & Advance Tax",
        "category": "Tax Collection",
        "is_premium": True,
        "summary": "Tax deducted at source on specified payments and remittal obligations.",
        "key_points": [
            "The payer withholds tax when making qualifying payments and remits it to KRA.",
            "Withholding certificates serve as proof of tax deducted for the payee.",
            "Late withholding or late remittance can trigger penalties and interest.",
        ],
    },
]


@router.get("")
def list_tax_notes(email: Optional[str] = Query(default=None)):
    active = has_active_plan(email) if email else False
    items = []
    for note in TAX_NOTES:
        locked = note["is_premium"] and not active
        items.append(
            {
                "id": note["id"],
                "title": note["title"],
                "category": note["category"],
                "is_premium": note["is_premium"],
                "locked": locked,
                "summary": note["summary"],
            }
        )
    return {"plan_active": active, "notes": items}


@router.get("/{note_id}")
def get_tax_note(note_id: str, email: Optional[str] = Query(default=None)):
    note = next((n for n in TAX_NOTES if n["id"] == note_id), None)
    if not note:
        raise HTTPException(status_code=404, detail="Tax note not found.")

    active = has_active_plan(email) if email else False
    if note["is_premium"] and not active:
        raise HTTPException(
            status_code=403,
            detail="Active 30-day plan required to view this study note.",
        )

    return {**note, "locked": False}