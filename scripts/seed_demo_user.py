"""
seed_demo_user.py
=================
Creates a demo user in the persona database with 30 pre-baked chunks.
Used in every rehearsal and demo to have realistic data ready instantly.

Usage:
    cd scripts
    python seed_demo_user.py

Requirements:
    pip install sqlalchemy psycopg2-binary python-dotenv
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── config ────────────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/persona"
).replace("/app", "/persona")  # ensure we use persona DB not app DB

DEMO_USER_EMAIL = "demo@persona.ai"
DEMO_PERSONA_NAME = "Demo Persona"
NUM_CHUNKS = 30

# ── sample chunk texts ────────────────────────────────────────────────────────

SAMPLE_CHUNKS = [
    "I grew up in Lahore and moved to London for university.",
    "My favourite food is biryani — specifically my grandmother's recipe.",
    "I work in AI research and have been building neural networks since 2018.",
    "I run 5km every morning before breakfast.",
    "My biggest fear is losing the people I love.",
    "I speak Urdu, English, and a little French.",
    "I prefer tea over coffee — always loose leaf, never bags.",
    "I read at least one book per week, mostly non-fiction.",
    "My favourite author is Haruki Murakami.",
    "I play guitar — mostly fingerstyle acoustic.",
    "I am an introvert who enjoys deep one-on-one conversations.",
    "I believe in doing fewer things but doing them very well.",
    "My morning routine starts at 6am without an alarm.",
    "I have two younger sisters who are both doctors.",
    "I prefer mountains over beaches for holidays.",
    "My first programming language was Python at age 16.",
    "I mentor junior engineers every Friday afternoon.",
    "I journal every night before sleeping.",
    "I am working on building an AI that understands people deeply.",
    "I dislike small talk but love talking about ideas.",
    "My hero is Richard Feynman — curiosity without ego.",
    "I have lived in four countries across three continents.",
    "I believe sleep is the most underrated performance tool.",
    "I spend weekends cooking elaborate meals for friends.",
    "I hate wasting food — I always finish what is on my plate.",
    "My workspace is completely minimalist — just a laptop and a notebook.",
    "I think the best ideas come during long walks.",
    "I am building this project because I want AI to feel human.",
    "I value honesty above everything else in relationships.",
    "My long-term goal is to build something that outlasts me.",
]


# ── main ─────────────────────────────────────────────────────────────────────

def seed():
    print(f"Connecting to: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Check if demo user already exists
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": DEMO_USER_EMAIL}
        ).fetchone()

        if existing:
            print(f"Demo user already exists: {DEMO_USER_EMAIL}")
            user_id = existing[0]
        else:
            # Create demo user
            user_id = uuid.uuid4()
            db.execute(
                text("""
                    INSERT INTO users (id, email, created_at, is_active)
                    VALUES (:id, :email, :created_at, :is_active)
                """),
                {
                    "id": user_id,
                    "email": DEMO_USER_EMAIL,
                    "created_at": datetime.now(timezone.utc),
                    "is_active": True,
                }
            )
            print(f"Created demo user: {DEMO_USER_EMAIL} ({user_id})")

        # Create demo persona
        persona_id = uuid.uuid4()
        db.execute(
            text("""
                INSERT INTO personas (id, user_id, name, persona_blob, created_at, is_active)
                VALUES (:id, :user_id, :name, :blob, :created_at, :is_active)
            """),
            {
                "id": persona_id,
                "user_id": user_id,
                "name": DEMO_PERSONA_NAME,
                "blob": '{"type": "demo", "version": 1}',
                "created_at": datetime.now(timezone.utc),
                "is_active": True,
            }
        )
        print(f"Created demo persona: {DEMO_PERSONA_NAME} ({persona_id})")

        # Create 30 ingestion jobs and messages (simulating chunks)
        for i, chunk_text in enumerate(SAMPLE_CHUNKS[:NUM_CHUNKS]):
            # Create message representing a chunk
            message_id = uuid.uuid4()
            db.execute(
                text("""
                    INSERT INTO messages (id, user_id, persona_id, role, content, created_at)
                    VALUES (:id, :user_id, :persona_id, :role, :content, :created_at)
                """),
                {
                    "id": message_id,
                    "user_id": user_id,
                    "persona_id": persona_id,
                    "role": "assistant",
                    "content": chunk_text,
                    "created_at": datetime.now(timezone.utc),
                }
            )

        print(f"Created {NUM_CHUNKS} demo chunks as messages")

        # Create a completed ingestion job
        job_id = uuid.uuid4()
        db.execute(
            text("""
                INSERT INTO ingestion_jobs (id, user_id, status, source, created_at)
                VALUES (:id, :user_id, :status, :source, :created_at)
            """),
            {
                "id": job_id,
                "user_id": user_id,
                "status": "indexed",
                "source": "seed_demo_user.py",
                "created_at": datetime.now(timezone.utc),
            }
        )
        print(f"Created demo ingestion job: {job_id} (status: indexed)")

        db.commit()
        print("\n✅ Seed complete!")
        print(f"   User:    {DEMO_USER_EMAIL}")
        print(f"   Persona: {DEMO_PERSONA_NAME}")
        print(f"   Chunks:  {NUM_CHUNKS}")
        print(f"\nLogin with: {DEMO_USER_EMAIL}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed()