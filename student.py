import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from database import create_user, get_user_by_email, has_active_subscription
from security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/students", tags=["Students"])


class StudentRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=1, max_length=128)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_student(data: StudentRegister):
    if "@" not in data.email or "." not in data.email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Enter a valid email address.")

    if get_user_by_email(data.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    try:
        user = create_user(
            full_name=data.full_name,
            email=data.email,
            password_hash=hash_password(data.password),
            role="student",
        )
        token = create_access_token(user["id"], user["role"])
        return {
            "message": "Student account created successfully.",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
            },
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")


@router.post("/login")
def login_student(data: LoginRequest):
    user = get_user_by_email(data.email)
    if not user or user["role"] != "student" or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    active, expires_at = has_active_subscription(user["id"])
    token = create_access_token(user["id"], user["role"])
    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "subscription_active": active,
        "subscription_expires_at": expires_at,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
        },
    }


@router.get("/me")
def student_profile(current_user: dict = Depends(get_current_user)):
    active, expires_at = has_active_subscription(current_user["id"])
    return {
        "id": current_user["id"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "subscription_active": active,
        "subscription_expires_at": expires_at,
    }