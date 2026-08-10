import os
import subprocess
import time
import uvicorn
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from routers.auth import router as auth_router
from routers.persona import router as persona_router

app = FastAPI(title="Persona AI API")

_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "").split(",")
    if o.strip()
]
if not _cors_origins:
    _cors_origins = [
        "http://localhost:3002",
        "http://localhost:3000",
    ]
_production_web = "https://web-production-4e2b6.up.railway.app"
if _production_web not in _cors_origins:
    _cors_origins.append(_production_web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Langfuse tracing
_langfuse = None
try:
    from langfuse import Langfuse
    _langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "http://langfuse:3000"),
    )
    print("Langfuse initialized.")
except Exception as e:
    print(f"Langfuse init warning: {e}")


@app.middleware("http")
async def langfuse_tracing(request: Request, call_next):
    if not _langfuse or request.url.path in ("/healthz", "/ping", "/docs", "/openapi.json"):
        return await call_next(request)

    start_time = time.time()
    trace_id = str(uuid.uuid4())

    trace = _langfuse.trace(
        id=trace_id,
        name=f"{request.method} {request.url.path}",
        metadata={"method": request.method, "path": request.url.path},
    )

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000
    trace.span(
        name="request",
        input={"method": request.method, "path": request.url.path},
        output={"status": response.status_code},
        metadata={"duration_ms": round(duration_ms, 2)},
    )
    trace.update(metadata={"status_code": response.status_code, "duration_ms": round(duration_ms, 2)})

    return response

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from storage.client import get_presigned_url, upload_bytes, R2_INGEST_BUCKET
from ingest.runner import create_job, JobStatus

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)

# Shared engine for health checks
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5}, pool_pre_ping=True)
    return _engine


# Register routers
from routers.ingest import router as ingest_router
from routers.voice import router as voice_router
from routers.chat import router as chat_router
from routers.questions import router as questions_router
from routers.feedback import router as feedback_router

app.include_router(chat_router)
app.include_router(questions_router)
app.include_router(feedback_router)
app.include_router(ingest_router)
app.include_router(voice_router)
app.include_router(auth_router)
app.include_router(persona_router)


@app.get("/healthz")
def health_check():
    # Git SHA
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        sha = "unknown"

    # DB ping
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        from qdrant_client import QdrantClient
        qc = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        qc.get_collections()
        qdrant_ok = True
    except Exception:
        qdrant_ok = False

    # Redis ping
    try:
        import redis as redis_lib
        r = redis_lib.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    all_ok = db_ok and qdrant_ok and redis_ok
    any_ok = db_ok or qdrant_ok or redis_ok

    return JSONResponse(
        status_code=200 if any_ok else 503,
        content={
            "status": "ok" if all_ok else "degraded",
            "sha": sha,
            "db": db_ok,
            "qdrant": qdrant_ok,
            "redis": redis_ok,
        }
    )


@app.get("/ping")
def ping():
    return {"pong": True}


@app.get("/")
def root():
    return {"message": "Persona AI API is running"}


@app.post("/ingest/presign")
def get_upload_url(filename: str, content_type: str = "application/pdf"):
    key = f"uploads/{uuid.uuid4()}/{filename}"
    url = get_presigned_url(key=key, bucket=R2_INGEST_BUCKET, expires_in=3600, method="put_object")
    return {"upload_url": url, "key": key}


def run_migrations():
    print("Running Alembic migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=os.path.dirname(__file__),
        capture_output=True,
        text=True,
        timeout=30
    )
    print(result.stdout)
    if result.returncode != 0:
        print("Migration error:", result.stderr)
        raise RuntimeError("Migrations failed")
    print("Migrations complete.")


@app.on_event("startup")
def startup_event():
    try:
        run_migrations()
    except Exception as e:
        print(f"Migration warning: {e}")

    try:
        from services.ai.rag.retriever import ensure_collection
        ensure_collection()
        print("Qdrant collection ensured.")
    except Exception as e:
        print(f"Qdrant collection warning: {e}")


if __name__ == "__main__":
    reload = os.getenv("RELOAD", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        reload=reload
    )
