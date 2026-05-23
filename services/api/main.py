import os
import subprocess
import uvicorn
from fastapi import FastAPI
from storage.client import get_presigned_url, upload_bytes, R2_INGEST_BUCKET
from ingest.runner import create_job, JobStatus
import uuid

app = FastAPI(title="Persona AI API")


@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/ping")
def ping():
    return {"pong": True}

@app.get("/")
def root():
    return {"message": "Persona AI API is running"}


@app.post("/ingest/presign")
def get_upload_url(filename: str, content_type: str = "application/pdf"):
    """
    Get a presigned URL for direct upload to R2.
    Frontend uses this to upload files directly to R2 without going through API.
    """
    key = f"uploads/{uuid.uuid4()}/{filename}"
    url = get_presigned_url(
        key=key,
        bucket=R2_INGEST_BUCKET,
        expires_in=3600,
        method="put_object"
    )
    return {"upload_url": url, "key": key}


@app.get("/ingest/job/{job_id}")
def get_job_status(job_id: str):
    """Get the current status of an ingestion job."""
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job status endpoint — DB connection coming in next sprint"
    }


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
