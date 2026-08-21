import os
import jwt
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

JWT_SECRET = os.getenv("JWT_SECRET", "persona-ai-local-jwt-secret-key-2024")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/persona")

_connect_args = {"connect_timeout": 5} if DATABASE_URL.startswith("postgresql") else {}
_engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)

security = HTTPBearer(auto_error=False)


def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        with _engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, email FROM users WHERE id = :uid AND is_active = true"),
                {"uid": user_id}
            ).fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Account not found. Please sign up again.")
    except HTTPException:
        raise
    except Exception:
        pass

    return {"user_id": user_id, "email": email}
