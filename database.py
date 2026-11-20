from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

# Simple in-memory store for quick testing; swap for SQLite/Postgres in production
USERS_DB: Dict[str, Dict[str, Any]] = {}
PAYMENTS_DB: list[Dict[str, Any]] = []


def get_user(email: str) -> Optional[Dict[str, Any]]:
    """Return an existing user without creating a new record."""
    return USERS_DB.get(email.strip().lower())


def get_or_create_user(email: str) -> Dict[str, Any]:
    email_key = email.strip().lower()
    if email_key not in USERS_DB:
        USERS_DB[email_key] = {
            "email": email_key,
            "plan_active": False,
            "plan_expires_at": None,
        }
    return USERS_DB[email_key]


def activate_plan(email: str, days: int = 30) -> Dict[str, Any]:
    user = get_or_create_user(email)
    now = datetime.now(timezone.utc)
    current_expiry = user.get("plan_expires_at")
    base_time = (
        current_expiry
        if isinstance(current_expiry, datetime) and current_expiry > now
        else now
    )
    expires_at = base_time + timedelta(days=days)
    user["plan_active"] = True
    user["plan_expires_at"] = expires_at
    return user


def has_active_plan(email: str) -> bool:
    user = get_user(email)
    if not user:
        return False
    expires_at = user.get("plan_expires_at")
    if not user.get("plan_active") or not isinstance(expires_at, datetime):
        user["plan_active"] = False
        return False
    if datetime.now(timezone.utc) >= expires_at:
        user["plan_active"] = False
        return False
    return True


def record_payment(
    email: str,
    mpesa_code: str,
    amount_kes: int,
    status: str = "activated",
) -> Dict[str, Any]:
    record = {
        "email": email.strip().lower(),
        "mpesa_code": mpesa_code.strip().upper(),
        "amount_kes": amount_kes,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
    }
    PAYMENTS_DB.append(record)
    return record