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
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

_connect_args = {"connect_timeout": 5} if DATABASE_URL.startswith("postgresql") else {}
_engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)

router = APIRouter(prefix="/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


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
    try:
        with _engine.connect() as conn:
            existing = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": request.email}
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")

            user_id = str(uuid.uuid4())
            password_hash = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()
            now = datetime.now(timezone.utc)
            conn.execute(
                text("INSERT INTO users (id, email, password_hash, full_name, auth_provider, created_at, is_active) VALUES (:id, :email, :pw, :name, 'local', :now, true)"),
                {"id": user_id, "email": request.email, "pw": password_hash, "name": request.full_name, "now": now}
            )

            # Auto-create free subscription (best effort)
            try:
                plan = conn.execute(
                    text("SELECT id FROM subscription_plans WHERE name = 'free' LIMIT 1")
                ).fetchone()
                if plan:
                    sub_id = str(uuid.uuid4())
                    conn.execute(
                        text("""INSERT INTO user_subscriptions
                            (id, user_id, plan_id, status, twins_used, messages_today, messages_used,
                             current_period_start, current_period_end, created_at, updated_at)
                            VALUES (:id, :uid, :pid, 'active', 0, 0, 0, :now, :now, :now, :now)"""),
                        {"id": sub_id, "uid": user_id, "pid": str(plan[0]), "now": now}
                    )
            except Exception:
                pass

            conn.commit()

        token = _create_token(user_id, request.email)
        return {
            "user_id": user_id,
            "email": request.email,
            "access_token": token,
            "message": "Signup successful!"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/login")
def login(request: LoginRequest):
    try:
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

        # Ensure user has a subscription (for users created before auto-subscribe)
        try:
            with _engine.connect() as conn:
                existing_sub = conn.execute(
                    text("SELECT id FROM user_subscriptions WHERE user_id = :uid LIMIT 1"),
                    {"uid": user_id}
                ).fetchone()
                if not existing_sub:
                    plan = conn.execute(
                        text("SELECT id FROM subscription_plans WHERE name = 'free' LIMIT 1")
                    ).fetchone()
                    if plan:
                        sub_id = str(uuid.uuid4())
                        now = datetime.now(timezone.utc)
                        conn.execute(
                            text("""INSERT INTO user_subscriptions
                                (id, user_id, plan_id, status, twins_used, messages_today, messages_used,
                                 current_period_start, current_period_end, created_at, updated_at)
                                VALUES (:id, :uid, :pid, 'active', 0, 0, 0, :now, :now, :now, :now)"""),
                            {"id": sub_id, "uid": user_id, "pid": str(plan[0]), "now": now}
                        )
                        conn.commit()
        except Exception:
            pass

        token = _create_token(user_id, email)
        return {
            "user_id": user_id,
            "email": email,
            "access_token": token,
            "message": "Login successful!"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully!"}


class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    with _engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": request.email}
        ).fetchone()

    if not row:
        return {"message": "If an account exists with that email, a reset link has been sent."}

    reset_token = jwt.encode(
        {
            "sub": str(row[0]),
            "email": request.email,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "purpose": "password_reset",
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    print(f"[PASSWORD RESET] Token for {request.email}: {reset_token}")
    print(f"[PASSWORD RESET] Frontend should redirect to: /reset-password?token={reset_token}")

    return {"message": "If an account exists with that email, a reset link has been sent."}


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    try:
        payload = jwt.decode(request.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset link has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid reset link")

    if payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid reset link")

    user_id = payload["sub"]
    new_hash = bcrypt.hashpw(request.new_password.encode(), bcrypt.gensalt()).decode()

    with _engine.connect() as conn:
        conn.execute(
            text("UPDATE users SET password_hash = :pw WHERE id = :id"),
            {"pw": new_hash, "id": user_id}
        )
        conn.commit()

    return {"message": "Password reset successful! You can now sign in."}


class GoogleLoginRequest(BaseModel):
    credential: str


@router.post("/google")
def google_login(request: GoogleLoginRequest):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        idinfo = id_token.verify_oauth2_token(
            request.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="google-auth library not installed")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    if idinfo.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise HTTPException(status_code=401, detail="Invalid token issuer")

    google_sub = idinfo["sub"]
    email = idinfo["email"]
    full_name = idinfo.get("name", "")
    avatar_url = idinfo.get("picture", "")
    email_verified = idinfo.get("email_verified", False)

    if not email_verified:
        raise HTTPException(status_code=401, detail="Google email not verified")

    with _engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, email FROM users WHERE google_sub = :sub"),
            {"sub": google_sub}
        ).fetchone()

        if not row:
            row = conn.execute(
                text("SELECT id, email FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()

            if row:
                user_id = str(row[0])
                conn.execute(
                    text("""UPDATE users SET google_sub = :sub, auth_provider = 'google',
                             full_name = :name, avatar_url = :avatar
                             WHERE id = :id"""),
                    {"sub": google_sub, "name": full_name, "avatar": avatar_url, "id": user_id}
                )
                conn.commit()
            else:
                user_id = str(uuid.uuid4())
                conn.execute(
                    text("""INSERT INTO users (id, email, full_name, avatar_url, auth_provider, google_sub, created_at, is_active)
                             VALUES (:id, :email, :name, :avatar, 'google', :sub, :now, true)"""),
                    {"id": user_id, "email": email, "name": full_name,
                     "avatar": avatar_url, "sub": google_sub, "now": datetime.now(timezone.utc)}
                )
                conn.commit()
        else:
            user_id = str(row[0])

    token = _create_token(user_id, email)
    return {
        "user_id": user_id,
        "email": email,
        "access_token": token,
        "message": "Google login successful!"
    }
