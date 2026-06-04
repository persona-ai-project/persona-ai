import os
import subprocess
import uvicorn
import uuid
 
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from storage.client import get_presigned_url, upload_bytes, R2_INGEST_BUCKET
from ingest.runner import create_job, JobStatus
 
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)
 
app = FastAPI(title="Persona AI API")
 
# Register routers
from routers.ingest import router as ingest_router
from routers.voice import router as voice_router
app.include_router(ingest_router)
app.include_router(voice_router)
 
 
@app.get("/healthz")
def health_check():
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        sha = "unknown"
 
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
 
    try:
        from qdrant_client import QdrantClient
        qc = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
        qc.get_collections()
        qdrant_ok = True
    except Exception:
        qdrant_ok = False
 
    try:
        import redis as redis_lib
        r = redis_lib.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
 
    all_ok = db_ok and qdrant_ok and redis_ok
    return JSONResponse(
        status_code=200 if all_ok else 503,
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
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("Migration error:", result.stderr)
        raise RuntimeError("Migrations failed")
    print("Migrations complete.")
 
 
if __name__ == "__main__":
    run_migrations()
    reload = os.getenv("RELOAD", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        reload=reload
    )