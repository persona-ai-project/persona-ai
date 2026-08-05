import os
import uuid
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/persona")
JWT_SECRET = os.getenv("JWT_SECRET", "persona-ai-local-jwt-secret-key-2024")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "72"))

_engine = create_engine(DATABASE_URL)

router = APIRouter(prefix="/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/signup")
def signup(request: SignUpRequest):
    with _engine.connect() as conn:
        existing = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": request.email}
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()
        conn.execute(
            text("INSERT INTO users (id, email, password_hash, created_at, is_active) VALUES (:id, :email, :pw, :now, true)"),
            {"id": user_id, "email": request.email, "pw": password_hash, "now": datetime.now(timezone.utc)}
        )
        conn.commit()

    token = _create_token(user_id, request.email)
    return {
        "user_id": user_id,
        "email": request.email,
        "access_token": token,
        "message": "Signup successful!"
    }


@router.post("/login")
def login(request: LoginRequest):
    with _engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, email, password_hash FROM users WHERE email = :email"),
            {"email": request.email}
        ).fetchone()

    if not row:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    user_id, email, password_hash = row
    user_id = str(user_id)
    if not password_hash or not bcrypt.checkpw(request.password.encode(), password_hash.encode()):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = _create_token(user_id, email)
    return {
        "user_id": user_id,
        "email": email,
        "access_token": token,
        "message": "Login successful!"
    }


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully!"}
