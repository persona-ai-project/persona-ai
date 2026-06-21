import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Supabase client
from supabase import create_client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

router = APIRouter(prefix="/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
def signup(request: SignUpRequest):
    """Register a new user via Supabase Auth."""
    try:
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })
        return {
            "user_id": response.user.id,
            "email": response.user.email,
            "message": "Signup successful!"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(request: LoginRequest):
    """Login user via Supabase Auth."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        return {
            "user_id": response.user.id,
            "email": response.user.email,
            "access_token": response.session.access_token,
            "message": "Login successful!"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
def logout(token: str):
    """Logout user."""
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))