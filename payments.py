import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database import activate_plan, get_or_create_user, record_payment

router = APIRouter(prefix="/payments", tags=["Payments"])

MPESA_NUMBER = os.getenv("TAXCLASS_MPESA_NUMBER", "0700566525")
PLAN_PRICE_KES = int(os.getenv("TAXCLASS_PLAN_PRICE_KES", "500"))
PLAN_DAYS = int(os.getenv("TAXCLASS_PLAN_DAYS", "30"))


class PaymentSubmitRequest(BaseModel):
    email: EmailStr
    mpesa_code: str
    amount_kes: int = PLAN_PRICE_KES


@router.get("/instructions")
def payment_instructions():
    return {
        "mpesa_number": MPESA_NUMBER,
        "amount_kes": PLAN_PRICE_KES,
        "duration_days": PLAN_DAYS,
        "message": f"Send KES {PLAN_PRICE_KES} to {MPESA_NUMBER} for {PLAN_DAYS} days of TaxClass Kenya access.",
    }


@router.post("/submit")
def submit_payment(payload: PaymentSubmitRequest):
    if payload.amount_kes < PLAN_PRICE_KES:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum payment is KES {PLAN_PRICE_KES} for {PLAN_DAYS} days.",
        )

    record = record_payment(
        email=payload.email,
        mpesa_code=payload.mpesa_code,
        amount_kes=payload.amount_kes,
        status="activated",
    )
    user = activate_plan(payload.email, days=PLAN_DAYS)

    return {
        "status": "success",
        "plan_days": PLAN_DAYS,
        "expires_at": user["plan_expires_at"].isoformat(),
        "payment": record,
    }


@router.get("/status/{email}")
def check_status(email: str):
    user = get_or_create_user(email)
    return {
        "email": user["email"],
        "plan_active": user["plan_active"],
        "expires_at": user["plan_expires_at"].isoformat() if user["plan_expires_at"] else None,
    }
