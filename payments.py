
import os
import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from database import get_user_by_email, get_connection

router = APIRouter(prefix="/payments", tags=["Payments"])

MPESA_NUMBER = os.getenv(
    "TAXCLASS_MPESA_NUMBER",
    "0700566525"
)

PLAN_PRICE = 500
PLAN_DURATION_DAYS = 30

class PaymentSubmission(BaseModel):
    email: EmailStr
    mpesa_code: str = Field(min_length=8, max_length=20)
    amount_kes: int = Field(gt=0)

@router.get("/instructions")
def payment_instructions():
    return {
        "payment_method": "M-Pesa",
        "paybill_or_phone": MPESA_NUMBER,
        "amount_kes": PLAN_PRICE,
        "subscription_duration": PLAN_DURATION_DAYS,
        "currency": "KES",
        "instructions": (
            "Send KSh 500 using the displayed M-Pesa number. "
            "Submit your transaction code for verification."
        )
    }

@router.post("/submit")
def submit_payment(payment: PaymentSubmission):

    if payment.amount_kes != PLAN_PRICE:
        raise HTTPException(
            status_code=400,
            detail=f"Please submit the exact amount of KSh {PLAN_PRICE}."
        )

    user = get_user_by_email(str(payment.email))

    if not user or user["role"] != "student":
        raise HTTPException(
            status_code=404,
            detail="Student account not found."
        )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO payments (
                user_id,
                mpesa_code,
                amount_kes,
                status
            )
            VALUES (?, ?, ?, 'pending')
            """,
            (
                user["id"],
                payment.mpesa_code.strip().upper(),
                payment.amount_kes
            )
        )

        connection.commit()

        return {
            "message": "Payment submitted successfully.",
            "payment_id": cursor.lastrowid,
            "status": "pending",
            "note": "Your payment must be verified before subscription activation."
        }

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="This M-Pesa transaction code has already been submitted."
        )

    finally:
        connection.close()