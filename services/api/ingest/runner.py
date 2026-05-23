"""
Ingestion Job State Machine
============================

Each ingestion job moves through the following states:

    queued → parsing → chunking → embedding → indexed
                                                  ↓
                                               failed (from any state)

State descriptions:
    queued    — job created, waiting to be picked up by a worker
    parsing   — document is being read and converted to raw text
    chunking  — raw text is being split into Chunk objects
    embedding — chunks are being converted to vectors via embedder
    indexed   — all vectors stored in Qdrant, job complete
    failed    — an error occurred at any stage, error stored in DB

Each state transition:
    1. Updates ingestion_jobs.status in Postgres
    2. Optionally updates ingestion_jobs.error if failed
    3. Logs the transition to Langfuse for observability

Database columns used:
    ingestion_jobs.id         — UUID job identifier
    ingestion_jobs.user_id    — who owns this job
    ingestion_jobs.status     — current state (string)
    ingestion_jobs.source     — original file path or URL
    ingestion_jobs.error      — error message if failed
    ingestion_jobs.created_at — when job was created
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session


# ── state definitions ─────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    QUEUED    = "queued"
    PARSING   = "parsing"
    CHUNKING  = "chunking"
    EMBEDDING = "embedding"
    INDEXED   = "indexed"
    FAILED    = "failed"


# Valid state transitions — only these moves are allowed
VALID_TRANSITIONS: dict[JobStatus, list[JobStatus]] = {
    JobStatus.QUEUED:    [JobStatus.PARSING,   JobStatus.FAILED],
    JobStatus.PARSING:   [JobStatus.CHUNKING,  JobStatus.FAILED],
    JobStatus.CHUNKING:  [JobStatus.EMBEDDING, JobStatus.FAILED],
    JobStatus.EMBEDDING: [JobStatus.INDEXED,   JobStatus.FAILED],
    JobStatus.INDEXED:   [],   # terminal state
    JobStatus.FAILED:    [],   # terminal state
}


# ── state machine ─────────────────────────────────────────────────────────────

class IngestionRunner:
    """
    Manages state transitions for a single ingestion job.

    Usage:
        runner = IngestionRunner(job_id=uuid, db=session)
        runner.transition(JobStatus.PARSING)
        # ... do parsing work ...
        runner.transition(JobStatus.CHUNKING)
        # ... do chunking work ...
        runner.transition(JobStatus.EMBEDDING)
        # ... do embedding work ...
        runner.transition(JobStatus.INDEXED)
    """

    def __init__(self, job_id: uuid.UUID, db: Session):
        self.job_id = job_id
        self.db = db

    def transition(
        self,
        new_status: JobStatus,
        error: Optional[str] = None,
    ) -> None:
        """
        Move the job to a new state.

        Args:
            new_status: The state to transition to
            error:      Error message (only used when transitioning to FAILED)

        Raises:
            ValueError: If the transition is not valid from the current state
        """
        from db.models.models import IngestionJob

        job = self.db.query(IngestionJob).filter(
            IngestionJob.id == self.job_id
        ).first()

        if not job:
            raise ValueError(f"Job {self.job_id} not found")

        current = JobStatus(job.status)

        # Validate the transition is allowed
        if new_status not in VALID_TRANSITIONS[current]:
            raise ValueError(
                f"Invalid transition: {current} → {new_status}. "
                f"Allowed: {VALID_TRANSITIONS[current]}"
            )

        # Update DB
        job.status = new_status.value
        if error:
            job.error = error

        self.db.commit()
        self.db.refresh(job)

        print(f"[IngestionRunner] Job {self.job_id}: {current} → {new_status}")

    def fail(self, error: str) -> None:
        """Convenience method to mark a job as failed with an error message."""
        self.transition(JobStatus.FAILED, error=error)


# ── standalone helper ─────────────────────────────────────────────────────────

def create_job(
    db: Session,
    user_id: uuid.UUID,
    source: str,
) -> uuid.UUID:
    """
    Create a new ingestion job in QUEUED state.

    Args:
        db:      Database session
        user_id: UUID of the user who owns the job
        source:  File path or URL being ingested

    Returns:
        UUID of the newly created job
    """
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

    print(f"[IngestionRunner] Created job {job.id} for user {user_id}")
    return job.id