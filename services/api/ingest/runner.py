from __future__ import annotations

import uuid
import os
import sys
import ssl
import time
import nltk
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add paths for P1's modules
AI_PATH = os.path.join(os.path.dirname(__file__), '..', 'services_ai')
ROOT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, AI_PATH)
sys.path.insert(0, ROOT_PATH)

from shared.contracts.chunk import Chunk

# NLTK setup
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)


from services.ai.rag.chunker import chunk_text


class JobStatus(str, Enum):
    QUEUED    = "queued"
    PARSING   = "parsing"
    CHUNKING  = "chunking"
    EMBEDDING = "embedding"
    INDEXED   = "indexed"
    FAILED    = "failed"


def _parse_file(file_path: str, source_type: str) -> str:
    path = Path(file_path)

    if source_type == "pdf":
        import pypdf
        reader = pypdf.PdfReader(file_path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    elif source_type == "docx":
        import docx as python_docx
        doc = python_docx.Document(file_path)
        return "\n\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())

    elif source_type in ("markdown", "md", "text", "txt"):
        return path.read_text(encoding="utf-8", errors="replace")

    elif source_type == "whatsapp":
        if "::" in file_path:
            actual_path, owner_name = file_path.split("::", 1)
        else:
            actual_path, owner_name = file_path, "unknown"
        from parsers.whatsapp import parse_whatsapp
        chunks = parse_whatsapp(actual_path, owner_name=owner_name)
        return "\n\n".join(c.text for c in chunks)

    elif source_type == "url":
        import trafilatura
        downloaded = trafilatura.fetch_url(file_path)
        return trafilatura.extract(downloaded) or ""

    else:
        raise ValueError(f"Unknown source_type: {source_type}")


def _update_status(db, job_id, status, error=None):
    from db.models.models import IngestionJob
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if job:
        job.status = status.value
        if error:
            job.error = error
        db.commit()
    time.sleep(0.5)
    print(f"[runner] Job {job_id} → {status.value}")


def create_job(db, user_id, source):
    from db.models.models import IngestionJob
    job = IngestionJob(
        id=uuid.uuid4(),
        user_id=user_id,
        status=JobStatus.QUEUED.value,
        source=source,
        created_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    print(f"[runner] Created job {job.id} for user {user_id}")
    return job.id


def run_ingestion_job(job_id, user_id, file_path, source_type, db_url="postgresql://postgres:postgres@localhost:5432/persona"):
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        _update_status(db, job_id, JobStatus.PARSING)
        raw_text = _parse_file(file_path, source_type)
        if not raw_text or not raw_text.strip():
            raise ValueError(f"Parser returned empty text for {file_path}")

        _update_status(db, job_id, JobStatus.CHUNKING)
        text_chunks = chunk_text(raw_text)
        if not text_chunks:
            raise ValueError("Chunker returned 0 chunks")

        now = datetime.now(timezone.utc)
        chunks = [
            Chunk(
                text=text,
                source=source_type,
                source_id=file_path,
                created_at=now,
                metadata={"chunk_index": i},
            )
            for i, text in enumerate(text_chunks)
            if text.strip()
        ]

        _update_status(db, job_id, JobStatus.EMBEDDING)
        sys.path.insert(0, "/app/services_ai")
        from rag.retriever import index as rag_index
        rag_index(user_id=str(user_id), chunks=chunks)

        _update_status(db, job_id, JobStatus.INDEXED)
        print(f"[runner] Job {job_id}: completed successfully")

    except Exception as e:
        error_msg = str(e)
        print(f"[runner] Job {job_id}: FAILED — {error_msg}")
        try:
            _update_status(db, job_id, JobStatus.FAILED, error=error_msg)
        except Exception:
            pass
    finally:
        db.close()