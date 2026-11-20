import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from payments import router as payments_router
from quiz import router as quiz_router
from tax_notes import router as tax_notes_router

APP_SECRET_KEY = os.getenv("TAXCLASS_SECRET_KEY", "dev-secret-change-in-prod")
ADMIN_EMAIL = os.getenv("TAXCLASS_ADMIN_EMAIL", "")
MPESA_NUMBER = os.getenv("TAXCLASS_MPESA_NUMBER", "0700566525")
PLAN_PRICE_KES = int(os.getenv("TAXCLASS_PLAN_PRICE_KES", "500"))
PLAN_DAYS = int(os.getenv("TAXCLASS_PLAN_DAYS", "30"))
HTTPS_ONLY = os.getenv("TAXCLASS_HTTPS_ONLY", "true").lower() == "true"

app = FastAPI(title="TaxClass Kenya")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tax_notes_router)
app.include_router(quiz_router)
app.include_router(payments_router)


@app.get("/")
def root():
    return {
        "app": "TaxClass Kenya",
        "status": "running",
        "mpesa_number": MPESA_NUMBER,
        "plan_price_kes": PLAN_PRICE_KES,
        "plan_days": PLAN_DAYS,
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "https_only": HTTPS_ONLY,
    }
