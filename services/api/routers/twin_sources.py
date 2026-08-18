"""
routers/twin_sources.py
=======================
Twin-aware source upload and ingestion.

Routes:
    POST   /twins/{twin_id}/sources/file       — multipart file upload
    POST   /twins/{twin_id}/sources/whatsapp    — WhatsApp .txt export
    POST   /twins/{twin_id}/sources/url         — URL ingestion
    GET    /twins/{twin_id}/sources              — list sources
    GET    /twins/{twin_id}/sources/{source_id}  — get source detail
    DELETE /twins/{twin_id}/sources/{source_id}  — delete source
    POST   /twins/{twin_id}/sources/{source_id}/reprocess — reprocess failed source
"""
from __future__ import annotations

import os
import sys
import uuid
import re
import tempfile
import pathlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.security import get_current_user
from storage.client import upload_bytes, get_presigned_url, R2_INGEST_BUCKET

ROOT_PATH = os.path.join(os.path.dirname(__file__), '..', '..')
AI_PATH = os.path.join(ROOT_PATH, 'services', 'ai')
sys.path.insert(0, ROOT_PATH)
sys.path.insert(0, AI_PATH)

router = APIRouter(prefix="/twins", tags=["twin-sources"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)

ALLOWED_EXTENSIONS = {
    ".pdf": "document",
    ".docx": "document",
    ".doc": "document",
    ".md": "document",
    ".markdown": "document",
    ".txt": "document",
}

SOURCE_TYPE_MAP = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
}

PROGRESS_MAP = {
    "pending": 0,
    "processing": 50,
    "ready": 100,
    "failed": -1,
}


# ── Models ──────────────────────────────────────────────────────────────────────

class SourceResponse(BaseModel):
    id: str
    twin_id: str
    source_type: str
    title: str | None
    url: str | None
    file_name: str | None
    file_size: int | None
    content_type: str | None
    status: str
    error: str | None
    chunk_count: int
    created_at: str
    updated_at: str
    progress_pct: int


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_db():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _verify_twin_owner(conn, twin_id: str, user_id: str):
    """Verify user owns the twin, raise 404 if not found."""
    row = conn.execute(
        text("SELECT id, owner_id, status FROM twins WHERE id = :id AND is_active = true"),
        {"id": twin_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Twin not found")
    if str(row[1]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return row


def _check_source_limit(conn, twin_id: str, user_id: str):
    """Check if user has reached source limit for their plan."""
    row = conn.execute(
        text("""SELECT sp.max_sources_per_twin, 
                       (SELECT COUNT(*) FROM sources WHERE twin_id = :tid) as current_count
                FROM user_subscriptions us
                JOIN subscription_plans sp ON us.plan_id = sp.id
                WHERE us.user_id = :uid AND us.status = 'active'"""),
        {"tid": twin_id, "uid": user_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="No active subscription")
    if row[1] >= row[0]:
        raise HTTPException(
            status_code=403,
            detail=f"Source limit reached ({row[0]}) for your plan. Upgrade to add more sources."
        )
    return row


def _detect_source_type(filename: str) -> tuple[str, str]:
    """Detect source type from file extension. Returns (content_type, parse_type)."""
    ext = os.path.splitext(filename.lower())[1]
    content_type = ALLOWED_EXTENSIONS.get(ext)
    if not content_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {list(ALLOWED_EXTENSIONS.keys())}"
        )
    parse_type = SOURCE_TYPE_MAP.get(ext, "text")
    return content_type, parse_type


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


def _parse_file(file_path: str, source_type: str) -> str:
    """Parse file content based on type."""
    from pathlib import Path
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
        from services.ai.parsers.whatsapp import parse_whatsapp
        chunks = parse_whatsapp(actual_path, owner_name=owner_name)
        return "\n\n".join(c.text for c in chunks)

    elif source_type == "url":
        import trafilatura
        downloaded = trafilatura.fetch_url(file_path)
        return trafilatura.extract(downloaded) or ""

    else:
        raise ValueError(f"Unknown source_type: {source_type}")


def _chunk_text(raw_text: str) -> list[str]:
    """Chunk text into processable pieces."""
    from services.ai.rag.chunker import chunk_text
    return chunk_text(raw_text)


def _index_chunks(user_id: str, twin_id: str, chunks: list, source_id: str):
    """Index chunks into Qdrant with twin_id."""
    from services.ai.rag.retriever import index as rag_index
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    chunk_objects = []
    for i, text in enumerate(chunks):
        if text.strip():
            chunk_objects.append({
                "text": text,
                "source": "twin_source",
                "source_id": source_id,
                "created_at": now,
                "metadata": {"chunk_index": i, "twin_id": twin_id},
            })

    # Create Chunk-like objects for the retriever
    class ChunkObj:
        def __init__(self, text, source, source_id, created_at, metadata):
            self.text = text
            self.source = source
            self.source_id = source_id
            self.created_at = created_at
            self.metadata = metadata

    chunk_objs = [ChunkObj(**c) for c in chunk_objects]
    return rag_index(user_id=user_id, chunks=chunk_objs, twin_id=twin_id, source_id=source_id)


def _extract_knowledge_items(raw_text: str, twin_id: str, source_id: str, content_type: str) -> list[dict]:
    """Extract knowledge items from raw text using LLM."""
    items = []

    # Simple extraction: split into paragraphs and treat each as a knowledge item
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]

    for i, paragraph in enumerate(paragraphs[:50]):  # Limit to 50 items per source
        if len(paragraph) < 20:  # Skip very short paragraphs
            continue

        # Determine content category
        item_type = "fact"  # default
        lower = paragraph.lower()
        if any(w in lower for w in ["i think", "i believe", "in my opinion", "i feel"]):
            item_type = "opinion"
        elif any(w in lower for w in ["i like", "i prefer", "i enjoy", "i love"]):
            item_type = "preference"
        elif any(w in lower for w in ["i remember", "that time", "back when"]):
            item_type = "memory"
        elif any(w in lower for w in ["i know how to", "i'm skilled at", "expertise"]):
            item_type = "skill"
        elif any(w in lower for w in ["my friend", "my colleague", "my partner"]):
            item_type = "relationship"
        elif any(w in lower for w in ["yesterday", "last week", "on monday", "in 2024"]):
            item_type = "event"

        items.append({
            "twin_id": twin_id,
            "source_id": source_id,
            "content_type": item_type,
            "content": paragraph[:2000],  # Limit length
            "confidence": 0.8,
            "metadata_": {"extracted_from": content_type, "paragraph_index": i},
        })

    return items


def _update_source_status(db, source_id: str, status: str, error: str = None, chunk_count: int = None):
    """Update source processing status."""
    updates = {"status": status, "updated_at": datetime.now(timezone.utc)}
    if error:
        updates["error"] = error
    if chunk_count is not None:
        updates["chunk_count"] = chunk_count

    set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
    db.execute(
        text(f"UPDATE sources SET {set_clause} WHERE id = :id"),
        {**updates, "id": source_id}
    )
    db.commit()


def _process_source_background(
    source_id: str,
    twin_id: str,
    user_id: str,
    file_path: str,
    source_type: str,
    db_url: str,
):
    """Background task to process an ingested source."""
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        _update_source_status(db, source_id, "processing")

        # Parse file
        raw_text = _parse_file(file_path, source_type)
        if not raw_text or not raw_text.strip():
            raise ValueError(f"Parser returned empty text for {file_path}")

        # Chunk text
        text_chunks = _chunk_text(raw_text)
        if not text_chunks:
            raise ValueError("Chunker returned 0 chunks")

        # Index in Qdrant
        chunk_count = _index_chunks(user_id, twin_id, text_chunks, source_id)

        # Extract knowledge items
        knowledge_items = _extract_knowledge_items(raw_text, twin_id, source_id, source_type)

        # Save knowledge items to DB
        for item in knowledge_items:
            db.execute(
                text("""INSERT INTO knowledge_items 
                    (id, twin_id, source_id, content_type, content, confidence, metadata, created_at, updated_at)
                    VALUES 
                    (:id, :twin_id, :source_id, :content_type, :content, :confidence, :metadata, :created_at, :updated_at)"""),
                {
                    "id": str(uuid.uuid4()),
                    "twin_id": twin_id,
                    "source_id": source_id,
                    "content_type": item["content_type"],
                    "content": item["content"],
                    "confidence": item["confidence"],
                    "metadata": item.get("metadata_"),
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        db.commit()

        _update_source_status(db, source_id, "ready", chunk_count=chunk_count)
        print(f"[twin_sources] Source {source_id}: completed ({chunk_count} chunks, {len(knowledge_items)} knowledge items)")

    except Exception as e:
        error_msg = str(e)
        print(f"[twin_sources] Source {source_id}: FAILED — {error_msg}")
        _update_source_status(db, source_id, "failed", error=error_msg)
    finally:
        db.close()


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.post("/{twin_id}/sources/file", status_code=202, response_model=SourceResponse)
async def upload_source_file(
    twin_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(default=None),
    current_user: dict = Depends(get_current_user),
):
    """Upload a file as a source for a twin."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)
        _check_source_limit(db, twin_id, user_id)

        # Detect source type
        content_type, parse_type = _detect_source_type(file.filename)

        # Read file bytes
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Upload to R2
        r2_key = f"twins/{twin_id}/sources/{uuid.uuid4()}/{file.filename}"
        upload_bytes(
            key=r2_key,
            data=file_bytes,
            content_type=file.content_type or "application/octet-stream",
            bucket=R2_INGEST_BUCKET,
        )

        # Create source record
        source_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        db.execute(
            text("""INSERT INTO sources 
                (id, twin_id, user_id, source_type, title, file_key, file_name, file_size, content_type, status, created_at, updated_at)
                VALUES 
                (:id, :twin_id, :user_id, :source_type, :title, :file_key, :file_name, :file_size, :content_type, :status, :created_at, :updated_at)"""),
            {
                "id": source_id,
                "twin_id": twin_id,
                "user_id": user_id,
                "source_type": "document",
                "title": title or file.filename,
                "file_key": r2_key,
                "file_name": file.filename,
                "file_size": len(file_bytes),
                "content_type": content_type,
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            }
        )
        db.commit()

        # Save file temporarily for background processing
        tmp_dir = tempfile.mkdtemp()
        tmp_path = pathlib.Path(tmp_dir) / file.filename
        tmp_path.write_bytes(file_bytes)

        # Start background ingestion
        background_tasks.add_task(
            _process_source_background,
            source_id=source_id,
            twin_id=twin_id,
            user_id=user_id,
            file_path=str(tmp_path),
            source_type=parse_type,
            db_url=DATABASE_URL,
        )

        return SourceResponse(
            id=source_id,
            twin_id=twin_id,
            source_type="document",
            title=title or file.filename,
            url=None,
            file_name=file.filename,
            file_size=len(file_bytes),
            content_type=content_type,
            status="pending",
            error=None,
            chunk_count=0,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            progress_pct=0,
        )
    finally:
        db.close()


@router.post("/{twin_id}/sources/whatsapp", status_code=202, response_model=SourceResponse)
async def upload_source_whatsapp(
    twin_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(default=None),
    owner_name: str = Form(default=""),
    current_user: dict = Depends(get_current_user),
):
    """Upload a WhatsApp export as a source for a twin."""
    user_id = current_user["id"]

    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="WhatsApp export must be a .txt file")

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)
        _check_source_limit(db, twin_id, user_id)

        # Read file bytes
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Upload to R2
        r2_key = f"twins/{twin_id}/sources/whatsapp/{uuid.uuid4()}/{file.filename}"
        upload_bytes(
            key=r2_key,
            data=file_bytes,
            content_type="text/plain",
            bucket=R2_INGEST_BUCKET,
        )

        # Create source record
        source_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        db.execute(
            text("""INSERT INTO sources 
                (id, twin_id, user_id, source_type, title, file_key, file_name, file_size, content_type, status, metadata, created_at, updated_at)
                VALUES 
                (:id, :twin_id, :user_id, :source_type, :title, :file_key, :file_name, :file_size, :content_type, :status, :metadata, :created_at, :updated_at)"""),
            {
                "id": source_id,
                "twin_id": twin_id,
                "user_id": user_id,
                "source_type": "whatsapp",
                "title": title or f"WhatsApp - {owner_name or 'All'}",
                "file_key": r2_key,
                "file_name": file.filename,
                "file_size": len(file_bytes),
                "content_type": "document",
                "status": "pending",
                "metadata": {"owner_name": owner_name},
                "created_at": now,
                "updated_at": now,
            }
        )
        db.commit()

        # Save file temporarily
        tmp_dir = tempfile.mkdtemp()
        tmp_path = pathlib.Path(tmp_dir) / file.filename
        tmp_path.write_bytes(file_bytes)

        # Pass owner_name via :: separator
        file_path_with_owner = f"{tmp_path}::{owner_name}" if owner_name else str(tmp_path)

        background_tasks.add_task(
            _process_source_background,
            source_id=source_id,
            twin_id=twin_id,
            user_id=user_id,
            file_path=file_path_with_owner,
            source_type="whatsapp",
            db_url=DATABASE_URL,
        )

        return SourceResponse(
            id=source_id,
            twin_id=twin_id,
            source_type="whatsapp",
            title=title or f"WhatsApp - {owner_name or 'All'}",
            url=None,
            file_name=file.filename,
            file_size=len(file_bytes),
            content_type="document",
            status="pending",
            error=None,
            chunk_count=0,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            progress_pct=0,
        )
    finally:
        db.close()


@router.post("/{twin_id}/sources/url", status_code=202, response_model=SourceResponse)
async def ingest_source_url(
    twin_id: str,
    background_tasks: BackgroundTasks,
    url: str,
    title: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    """Ingest a URL as a source for a twin."""
    user_id = current_user["id"]
    _validate_url(url)

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)
        _check_source_limit(db, twin_id, user_id)

        # Create source record
        source_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        db.execute(
            text("""INSERT INTO sources 
                (id, twin_id, user_id, source_type, title, url, content_type, status, created_at, updated_at)
                VALUES 
                (:id, :twin_id, :user_id, :source_type, :title, :url, :content_type, :status, :created_at, :updated_at)"""),
            {
                "id": source_id,
                "twin_id": twin_id,
                "user_id": user_id,
                "source_type": "url",
                "title": title or url[:200],
                "url": url,
                "content_type": "document",
                "status": "pending",
                "created_at": now,
                "updated_at": now,
            }
        )
        db.commit()

        background_tasks.add_task(
            _process_source_background,
            source_id=source_id,
            twin_id=twin_id,
            user_id=user_id,
            file_path=url,
            source_type="url",
            db_url=DATABASE_URL,
        )

        return SourceResponse(
            id=source_id,
            twin_id=twin_id,
            source_type="url",
            title=title or url[:200],
            url=url,
            file_name=None,
            file_size=None,
            content_type="document",
            status="pending",
            error=None,
            chunk_count=0,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            progress_pct=0,
        )
    finally:
        db.close()


@router.get("/{twin_id}/sources")
def list_sources(
    twin_id: str,
    current_user: dict = Depends(get_current_user),
    status: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all sources for a twin."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        query = """
            SELECT id, source_type, title, url, file_name, file_size, content_type,
                   status, error, chunk_count, created_at, updated_at
            FROM sources
            WHERE twin_id = :tid AND user_id = :uid
        """
        params = {"tid": twin_id, "uid": user_id, "limit": limit, "offset": offset}

        if status:
            query += " AND status = :status"
            params["status"] = status

        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        rows = db.execute(text(query), params).fetchall()

        # Get total count
        count_query = "SELECT COUNT(*) FROM sources WHERE twin_id = :tid AND user_id = :uid"
        count_params = {"tid": twin_id, "uid": user_id}
        if status:
            count_query += " AND status = :status"
            count_params["status"] = status
        total = db.execute(text(count_query), count_params).scalar()

        sources = []
        for r in rows:
            sources.append(SourceResponse(
                id=str(r[0]),
                twin_id=twin_id,
                source_type=r[1],
                title=r[2],
                url=r[3],
                file_name=r[4],
                file_size=r[5],
                content_type=r[6],
                status=r[7],
                error=r[8],
                chunk_count=r[9],
                created_at=str(r[10]),
                updated_at=str(r[11]),
                progress_pct=PROGRESS_MAP.get(r[7], 0),
            ))

        return {"sources": sources, "total": total, "limit": limit, "offset": offset}
    finally:
        db.close()


@router.get("/{twin_id}/sources/{source_id}", response_model=SourceResponse)
def get_source(
    twin_id: str,
    source_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get source detail."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        row = db.execute(
            text("""SELECT id, source_type, title, url, file_name, file_size, content_type,
                           status, error, chunk_count, created_at, updated_at
                    FROM sources
                    WHERE id = :id AND twin_id = :tid AND user_id = :uid"""),
            {"id": source_id, "tid": twin_id, "uid": user_id}
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Source not found")

        return SourceResponse(
            id=str(row[0]),
            twin_id=twin_id,
            source_type=row[1],
            title=row[2],
            url=row[3],
            file_name=row[4],
            file_size=row[5],
            content_type=row[6],
            status=row[7],
            error=row[8],
            chunk_count=row[9],
            created_at=str(row[10]),
            updated_at=str(row[11]),
            progress_pct=PROGRESS_MAP.get(row[7], 0),
        )
    finally:
        db.close()


@router.delete("/{twin_id}/sources/{source_id}")
def delete_source(
    twin_id: str,
    source_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a source and its associated data."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Verify source exists
        source = db.execute(
            text("SELECT id, file_key FROM sources WHERE id = :id AND twin_id = :tid AND user_id = :uid"),
            {"id": source_id, "tid": twin_id, "uid": user_id}
        ).fetchone()

        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # Delete from Qdrant
        try:
            from services.ai.rag.retriever import delete as rag_delete
            rag_delete(user_id=user_id, source_id=source_id)
        except Exception as e:
            print(f"[twin_sources] Qdrant delete warning: {e}")

        # Delete knowledge items
        db.execute(
            text("DELETE FROM knowledge_items WHERE source_id = :sid"),
            {"sid": source_id}
        )

        # Delete source
        db.execute(
            text("DELETE FROM sources WHERE id = :id"),
            {"id": source_id}
        )
        db.commit()

        return {"message": "Source deleted", "id": source_id}
    finally:
        db.close()


@router.post("/{twin_id}/sources/{source_id}/reprocess", status_code=202)
async def reprocess_source(
    twin_id: str,
    source_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Reprocess a failed source."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Get source
        source = db.execute(
            text("""SELECT id, file_key, source_type, file_name, status
                    FROM sources
                    WHERE id = :id AND twin_id = :tid AND user_id = :uid"""),
            {"id": source_id, "tid": twin_id, "uid": user_id}
        ).fetchone()

        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        if source[4] not in ("failed", "ready"):
            raise HTTPException(status_code=400, detail="Can only reprocess failed or ready sources")

        # Delete old knowledge items and Qdrant chunks
        db.execute(
            text("DELETE FROM knowledge_items WHERE source_id = :sid"),
            {"sid": source_id}
        )
        try:
            from services.ai.rag.retriever import delete as rag_delete
            rag_delete(user_id=user_id, source_id=source_id)
        except Exception:
            pass

        # Reset status
        _update_source_status(db, source_id, "pending")

        # Determine source_type for parser
        source_type_map = {"pdf": "pdf", "docx": "docx", "markdown": "markdown", "text": "text", "url": "url", "whatsapp": "whatsapp"}
        parse_type = source_type_map.get(source[2], "text")

        # Download from R2 if it's a file
        file_path = source[1]  # file_key or URL
        if source[2] != "url" and source[1]:
            # Download from R2 to temp file
            from storage.client import download_bytes
            file_bytes = download_bytes(key=source[1])
            tmp_dir = tempfile.mkdtemp()
            tmp_path = pathlib.Path(tmp_dir) / (source[3] or "file")
            tmp_path.write_bytes(file_bytes)
            file_path = str(tmp_path)

        background_tasks.add_task(
            _process_source_background,
            source_id=source_id,
            twin_id=twin_id,
            user_id=user_id,
            file_path=file_path,
            source_type=parse_type,
            db_url=DATABASE_URL,
        )

        return {"message": "Reprocessing started", "source_id": source_id}
    finally:
        db.close()
