"""
routers/ingest.py
=================
All ingestion HTTP routes.

Routes:
    POST   /ingest/file              — multipart file upload
    POST   /ingest/social/whatsapp   — WhatsApp .txt + owner_name
    POST   /ingest/url               — JSON {url: str}
    GET    /ingest/{job_id}          — job status + progress_pct
    DELETE /ingest/source/{source_id} — delete from DB + Qdrant
"""
from __future__ import annotations

import os
import sys
import uuid
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Path setup
ROOT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..')
AI_PATH   = os.path.join(ROOT_PATH, 'services', 'ai')
sys.path.insert(0, ROOT_PATH)
sys.path.insert(0, AI_PATH)


from storage.client import upload_bytes, get_presigned_url, R2_INGEST_BUCKET
from ingest.runner import create_job, run_ingestion_job, JobStatus

router = APIRouter(prefix="/ingest", tags=["ingestion"])

# ── DB setup ──────────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)

def get_db():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── progress mapping ──────────────────────────────────────────────────────────

PROGRESS = {
    "queued":    0,
    "parsing":   25,
    "chunking":  50,
    "embedding": 75,
    "indexed":   100,
    "failed":    -1,
}

ALLOWED_EXTENSIONS = {
    ".pdf":      "pdf",
    ".docx":     "docx",
    ".doc":      "docx",
    ".md":       "markdown",
    ".markdown": "markdown",
    ".txt":      "text",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _detect_source_type(filename: str) -> str:
    """Detect source type from file extension."""
    ext = os.path.splitext(filename.lower())[1]
    source_type = ALLOWED_EXTENSIONS.get(ext)
    if not source_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {list(ALLOWED_EXTENSIONS.keys())}"
        )
    return source_type


def _validate_url(url: str) -> str:
    """Validate URL format."""
    pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    if not pattern.match(url):
        raise HTTPException(status_code=400, detail=f"Invalid URL format: {url}")
    return url


def _get_job_or_404(db, job_id: str) -> dict:
    """Fetch job from DB or raise 404."""
    try:
        uid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    result = db.execute(
        text("""
            SELECT id, user_id, status, source, error, created_at
            FROM ingestion_jobs
            WHERE id = :id
        """),
        {"id": uid}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "job_id":       str(result[0]),
        "user_id":      str(result[1]),
        "status":       result[2],
        "source":       result[3],
        "error":        result[4],
        "created_at":   str(result[5]),
        "progress_pct": PROGRESS.get(result[2], 0),
    }


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("/file", status_code=202)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    """
    Upload a file for ingestion.
    Supports: .pdf, .docx, .doc, .md, .markdown, .txt

    Returns 202 immediately with job_id.
    Poll GET /ingest/{job_id} for progress.
    """
    # Detect source type from extension
    source_type = _detect_source_type(file.filename)

    # Read file bytes
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Upload to R2
    r2_key = f"ingestion/{user_id}/{uuid.uuid4()}/{file.filename}"
    upload_bytes(
        key=r2_key,
        data=file_bytes,
        content_type=file.content_type or "application/octet-stream",
        bucket=R2_INGEST_BUCKET,
    )

    # Create job in DB
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        uid = uuid.UUID(user_id)
        job_id = create_job(db, uid, source=r2_key)
    finally:
        db.close()

    # Save file temporarily for background runner
    import tempfile, pathlib
    tmp_dir = tempfile.mkdtemp()
    tmp_path = pathlib.Path(tmp_dir) / file.filename
    tmp_path.write_bytes(file_bytes)

    # Start background ingestion
    background_tasks.add_task(
        run_ingestion_job,
        job_id=job_id,
        user_id=uid,
        file_path=str(tmp_path),
        source_type=source_type,
        db_url=DATABASE_URL,
    )

    return {
        "job_id":  str(job_id),
        "status":  "queued",
        "source":  r2_key,
        "message": f"File uploaded. Poll /ingest/{job_id} for progress.",
    }


@router.post("/social/whatsapp", status_code=202)
async def ingest_whatsapp(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    owner_name: str = Form(default=""),
):
    """
    Upload a WhatsApp exported .txt chat file.
    Pass owner_name to filter to that person's messages only.

    Returns 202 immediately with job_id.
    """
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="WhatsApp export must be a .txt file"
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Upload to R2
    r2_key = f"ingestion/{user_id}/whatsapp/{uuid.uuid4()}/{file.filename}"
    upload_bytes(
        key=r2_key,
        data=file_bytes,
        content_type="text/plain",
        bucket=R2_INGEST_BUCKET,
    )

    # Create job in DB
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        uid = uuid.UUID(user_id)
        job_id = create_job(db, uid, source=r2_key)
    finally:
        db.close()

    # Save file temporarily
    import tempfile, pathlib
    tmp_dir = tempfile.mkdtemp()
    tmp_path = pathlib.Path(tmp_dir) / file.filename
    tmp_path.write_bytes(file_bytes)

    # Use :: separator to pass owner_name to runner
    file_path_with_owner = f"{tmp_path}::{owner_name}" if owner_name else str(tmp_path)

    background_tasks.add_task(
        run_ingestion_job,
        job_id=job_id,
        user_id=uid,
        file_path=file_path_with_owner,
        source_type="whatsapp",
        db_url=DATABASE_URL,
    )

    return {
        "job_id":     str(job_id),
        "status":     "queued",
        "source":     r2_key,
        "owner_name": owner_name or "all",
        "message":    f"WhatsApp file uploaded. Poll /ingest/{job_id} for progress.",
    }


@router.post("/url", status_code=202)
async def ingest_url(
    background_tasks: BackgroundTasks,
    url: str,
    user_id: str,
):
    """
    Ingest a web page by URL.
    trafilatura fetches and extracts the article text.

    Returns 202 immediately with job_id.
    """
    # Validate URL
    _validate_url(url)

    # Create job in DB
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        uid = uuid.UUID(user_id)
        job_id = create_job(db, uid, source=url)
    finally:
        db.close()

    background_tasks.add_task(
        run_ingestion_job,
        job_id=job_id,
        user_id=uid,
        file_path=url,
        source_type="url",
        db_url=DATABASE_URL,
    )

    return {
        "job_id":  str(job_id),
        "status":  "queued",
        "url":     url,
        "message": f"URL queued for ingestion. Poll /ingest/{job_id} for progress.",
    }


@router.get("/{job_id}")
def get_job_status(job_id: str):
    """
    Get ingestion job status and progress.

    Progress:
        queued    =   0%
        parsing   =  25%
        chunking  =  50%
        embedding =  75%
        indexed   = 100%
        failed    =  -1  (error)
    """
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        return _get_job_or_404(db, job_id)
    finally:
        db.close()


@router.delete("/source/{source_id}")
def delete_source(source_id: str, user_id: str):
    """
    Delete all data for a source:
    1. Removes ingestion_jobs rows from Postgres
    2. Removes chunks from Qdrant via P1's rag.delete()

    Args:
        source_id: The source key (R2 key or URL)
        user_id:   UUID of the user who owns the data
    """
    # Delete from Qdrant first (P1's retriever)
    try:
        sys.path.insert(0, "/app/services_ai")
        from rag.retriever import delete as rag_delete
        rag_delete(user_id=user_id, source=source_id)
        print(f"[ingest] Deleted chunks from Qdrant for source: {source_id}")
    except Exception as e:
        print(f"[ingest] Qdrant delete warning: {e}")

    # Delete from Postgres
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        result = db.execute(
            text("""
                DELETE FROM ingestion_jobs
                WHERE source = :source_id AND user_id = :user_id
            """),
            {"source_id": source_id, "user_id": uuid.UUID(user_id)}
        )
        db.commit()
        deleted_count = result.rowcount
    finally:
        db.close()

    return {
        "deleted":   True,
        "source_id": source_id,
        "jobs_removed": deleted_count,
        "message":   "Source deleted from DB and Qdrant",
    }