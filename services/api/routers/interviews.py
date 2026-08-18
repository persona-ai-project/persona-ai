"""
routers/interviews.py
=====================
Twin interview agent for knowledge extraction.

Routes:
    POST   /twins/{twin_id}/interviews                 — start new interview session
    POST   /twins/{twin_id}/interviews/{session_id}/message — send message and get follow-up
    GET    /twins/{twin_id}/interviews                  — list interview sessions
    GET    /twins/{twin_id}/interviews/{session_id}      — get session detail
    DELETE /twins/{twin_id}/interviews/{session_id}      — end/delete session
    GET    /twins/{twin_id}/interviews/topics            — list available topics
"""
from __future__ import annotations

import os
import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.security import get_current_user

router = APIRouter(prefix="/twins", tags=["interviews"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)


# ── Interview Topics ─────────────────────────────────────────────────────────────

INTERVIEW_TOPICS = {
    "background": {
        "name": "Background & History",
        "description": "Life story, upbringing, formative experiences",
        "system_prompt": """You are interviewing someone to learn about their background and life history.
Ask open-ended questions that help them share their story.
Focus on: where they grew up, family, education, career path, pivotal moments.
Be warm and curious. Follow up on interesting details they share.""",
        "knowledge_types": ["memory", "fact", "event"],
    },
    "personality": {
        "name": "Personality & Traits",
        "description": "Character, habits, how they interact with the world",
        "system_prompt": """You are interviewing someone to understand their personality and character.
Ask questions about how they approach situations, their habits, quirks, and interpersonal style.
Focus on: decision-making style, social preferences, stress responses, daily routines.
Be observational and insightful. Notice patterns in their responses.""",
        "knowledge_types": ["fact", "opinion", "preference"],
    },
    "opinions": {
        "name": "Opinions & Beliefs",
        "description": "Views on topics, values, philosophy",
        "system_prompt": """You are interviewing someone to understand their opinions and worldview.
Ask thoughtful questions about their views on various topics.
Focus on: values, hot takes, philosophical stances, what they care about.
Be respectful and non-judgmental. Explore nuances in their thinking.""",
        "knowledge_types": ["opinion", "preference"],
    },
    "skills": {
        "name": "Skills & Expertise",
        "description": "Abilities, knowledge areas, professional skills",
        "system_prompt": """You are interviewing someone to understand their skills and expertise.
Ask questions about what they're good at, what they've learned, and where they have deep knowledge.
Focus on: professional skills, hobbies they've mastered, unique knowledge, teaching ability.
Be specific. Ask for examples and details.""",
        "knowledge_types": ["skill", "fact"],
    },
    "relationships": {
        "name": "Relationships & People",
        "description": "Important people, social dynamics, communication style",
        "system_prompt": """You are interviewing someone to understand their important relationships and social world.
Ask about the people who matter to them and how they interact with others.
Focus on: family, friends, mentors, colleagues, communication preferences, conflict style.
Be sensitive. These are personal topics.""",
        "knowledge_types": ["relationship", "fact", "opinion"],
    },
    "interests": {
        "name": "Interests & Passions",
        "description": "Hobbies, media, things they love",
        "system_prompt": """You are interviewing someone to discover their interests and passions.
Ask about what they enjoy, what excites them, and how they spend their free time.
Focus on: hobbies, media consumption, creative pursuits, what makes them lose track of time.
Be enthusiastic. Share in their excitement.""",
        "knowledge_types": ["preference", "fact"],
    },
    "challenges": {
        "name": "Challenges & Growth",
        "description": "Obstacles overcome, lessons learned, personal growth",
        "system_prompt": """You are interviewing someone about challenges they've faced and how they've grown.
Ask thoughtful questions about obstacles, failures, and what they learned from them.
Focus on: difficult times, mistakes, resilience, wisdom gained.
Be empathetic. These are reflective topics.""",
        "knowledge_types": ["memory", "opinion", "fact"],
    },
    "goals": {
        "name": "Goals & Aspirations",
        "description": "Future plans, dreams, what drives them",
        "system_prompt": """You are interviewing someone about their goals and what they want to achieve.
Ask about their ambitions, dreams, and what motivates them.
Focus on: short-term goals, long-term vision, what success looks like to them, what drives them.
Be inspiring. Help them articulate their vision.""",
        "knowledge_types": ["opinion", "preference", "fact"],
    },
}


# ── Models ──────────────────────────────────────────────────────────────────────

class InterviewStart(BaseModel):
    topic: str | None = None  # topic key or None for general
    opening_message: str | None = None  # optional custom opening


class InterviewMessage(BaseModel):
    message: str


class InterviewResponse(BaseModel):
    session_id: str
    message_id: str
    role: str
    content: str
    follow_up: str | None = None
    knowledge_extracted: list[dict] = []
    questions_asked: int
    knowledge_count: int
    is_complete: bool


class InterviewSessionResponse(BaseModel):
    id: str
    twin_id: str
    topic: str | None
    topic_name: str | None
    status: str
    questions_asked: int
    messages_count: int
    items_extracted: int
    created_at: str
    updated_at: str


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
        text("SELECT id, owner_id, name FROM twins WHERE id = :id AND is_active = true"),
        {"id": twin_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Twin not found")
    if str(row[1]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return row


def _check_interview_limit(conn, twin_id: str, user_id: str):
    """Check if user has reached interview session limit."""
    row = conn.execute(
        text("""SELECT sp.max_interview_sessions,
                       (SELECT COUNT(*) FROM interview_sessions WHERE twin_id = :tid) as current_count
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
            detail=f"Interview limit reached ({row[0]}) for your plan. Complete or delete existing sessions."
        )
    return row


def _get_existing_knowledge(conn, twin_id: str) -> list[str]:
    """Get existing knowledge items to avoid repetition."""
    rows = conn.execute(
        text("""SELECT content FROM knowledge_items 
                WHERE twin_id = :tid AND is_active = true 
                ORDER BY created_at DESC LIMIT 50"""),
        {"tid": twin_id}
    ).fetchall()
    return [r[0] for r in rows]


def _get_interview_history(conn, session_id: str) -> list[dict]:
    """Get interview message history."""
    rows = conn.execute(
        text("""SELECT role, content FROM interview_messages 
                WHERE session_id = :sid ORDER BY created_at ASC"""),
        {"sid": session_id}
    ).fetchall()
    return [{"role": r[0], "content": r[1]} for r in rows]


def _generate_follow_up(
    twin_name: str,
    topic: str | None,
    history: list[dict],
    existing_knowledge: list[str],
    user_message: str,
) -> str:
    """Generate a context-aware follow-up question."""
    from llm.router import chat_completion

    topic_config = INTERVIEW_TOPICS.get(topic, {})
    system_prompt = topic_config.get("system_prompt", INTERVIEW_TOPICS["background"]["system_prompt"])

    # Build context
    knowledge_context = ""
    if existing_knowledge:
        knowledge_context = f"\n\nExisting knowledge about {twin_name}:\n" + "\n".join(f"- {k[:100]}" for k in existing_knowledge[:10])

    # Build conversation for LLM
    messages = [
        {"role": "system", "content": f"""{system_prompt}

You are interviewing someone to build a digital twin of {twin_name}.

IMPORTANT RULES:
1. Ask ONE question at a time
2. Build on what they just shared - don't repeat topics
3. Be conversational, not interrogative
4. If they share something interesting, explore it before moving on
5. After 5-8 exchanges, or when you have enough for this topic, say "Thank you, that's all I needed for this topic."

Your follow-up should be a single question that naturally extends the conversation.
Do NOT include any preamble or explanation. Just the question."""},
    ]

    # Add conversation history
    for msg in history[-6:]:  # Last 6 messages for context
        messages.append({"role": "assistant" if msg["role"] == "interviewer" else "user", "content": msg["content"]})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    # Add knowledge context if relevant
    if knowledge_context:
        messages.append({"role": "system", "content": f"Context - what we already know:{knowledge_context}"})

    try:
        response = chat_completion(messages, max_tokens=256)
        return response.strip()
    except Exception as e:
        print(f"[interviews] Follow-up generation failed: {e}")
        return f"That's interesting. Can you tell me more about that?"


def _extract_knowledge(
    twin_id: str,
    session_id: str,
    source_id: str,
    user_message: str,
    interviewer_response: str,
    topic: str | None,
) -> list[dict]:
    """Extract knowledge items from interview exchange."""
    from llm.router import chat_completion

    topic_config = INTERVIEW_TOPICS.get(topic, {})
    knowledge_types = topic_config.get("knowledge_types", ["fact", "opinion"])

    messages = [
        {"role": "system", "content": f"""Extract knowledge items from this interview exchange.
Return a JSON array of knowledge items. Each item should have:
- "content_type": one of {json.dumps(knowledge_types)}
- "content": the knowledge as a clear statement (not a quote)
- "confidence": 0.0 to 1.0 based on how clearly stated it is

Rules:
- Extract facts, opinions, preferences, memories, or skills
- Each item should be a standalone, clear statement
- Don't extract questions or vague statements
- Maximum 5 items per exchange
- Return ONLY the JSON array, no explanation

Example:
[
    {{"content_type": "fact", "content": "Grew up in Portland, Oregon", "confidence": 0.9}},
    {{"content_type": "opinion", "content": "Believes remote work is better for productivity", "confidence": 0.8}}
]"""},
        {"role": "user", "content": f"Interviewee said: {user_message}\n\nInterviewer asked: {interviewer_response}"}
    ]

    try:
        response = chat_completion(messages, max_tokens=512)
        content = response.strip()

        # Parse JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        items = json.loads(content)
        if not isinstance(items, list):
            items = [items]

        # Add IDs and metadata
        for item in items:
            item["id"] = str(uuid.uuid4())
            item["twin_id"] = twin_id
            item["source_id"] = source_id
            item["metadata_"] = {"from_interview": session_id, "topic": topic}

        return items[:5]  # Max 5 items
    except Exception as e:
        print(f"[interviews] Knowledge extraction failed: {e}")
        return []


def _save_knowledge_items(db, items: list[dict]):
    """Save extracted knowledge items to database."""
    for item in items:
        db.execute(
            text("""INSERT INTO knowledge_items 
                (id, twin_id, source_id, content_type, content, confidence, metadata, created_at, updated_at)
                VALUES 
                (:id, :twin_id, :source_id, :content_type, :content, :confidence, :metadata, :created_at, :updated_at)"""),
            {
                "id": item["id"],
                "twin_id": item["twin_id"],
                "source_id": item["source_id"],
                "content_type": item["content_type"],
                "content": item["content"],
                "confidence": item.get("confidence", 0.8),
                "metadata": item.get("metadata_"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
    db.commit()


def _index_interview_chunks(user_id: str, twin_id: str, session_id: str, messages: list[dict]):
    """Index interview Q&A pairs into Qdrant."""
    from services.ai.rag.retriever import index as rag_index

    chunks = []
    for msg in messages:
        if msg["role"] == "interviewer":
            continue
        # Find the corresponding interviewer question
        idx = messages.index(msg)
        question = messages[idx - 1]["content"] if idx > 0 and messages[idx - 1]["role"] == "interviewer" else ""

        chunk_text = f"Q: {question}\nA: {msg['content']}"
        chunks.append({
            "text": chunk_text,
            "source": "interview",
            "source_id": session_id,
            "created_at": datetime.now(timezone.utc),
            "metadata": {"twin_id": twin_id, "topic": "interview"},
        })

    if chunks:
        class ChunkObj:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        chunk_objs = [ChunkObj(**c) for c in chunks]
        rag_index(user_id=user_id, chunks=chunk_objs, twin_id=twin_id, source_id=session_id)


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.post("/{twin_id}/interviews", response_model=InterviewSessionResponse)
def start_interview(
    twin_id: str,
    body: InterviewStart | None = None,
    current_user: dict = Depends(get_current_user),
):
    """Start a new interview session for a twin."""
    user_id = current_user["id"]
    topic = body.topic if body else None

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)
        _check_interview_limit(db, twin_id, user_id)

        # Validate topic
        if topic and topic not in INTERVIEW_TOPICS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid topic. Available: {list(INTERVIEW_TOPICS.keys())}"
            )

        # Get twin name for context
        twin = db.execute(
            text("SELECT name FROM twins WHERE id = :id"),
            {"id": twin_id}
        ).fetchone()
        twin_name = twin[0] if twin else "the person"

        # Create session
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        db.execute(
            text("""INSERT INTO interview_sessions 
                (id, twin_id, user_id, status, topic, created_at, updated_at)
                VALUES (:id, :twin_id, :user_id, :status, :topic, :created_at, :updated_at)"""),
            {
                "id": session_id,
                "twin_id": twin_id,
                "user_id": user_id,
                "status": "active",
                "topic": topic,
                "created_at": now,
                "updated_at": now,
            }
        )
        db.commit()

        # Generate opening question
        topic_config = INTERVIEW_TOPICS.get(topic, {})
        topic_name = topic_config.get("name", "General")

        opening = body.opening_message if body and body.opening_message else None
        if not opening:
            from llm.router import chat_completion
            messages = [
                {"role": "system", "content": f"""You are starting an interview to learn about {twin_name} for their digital twin.
Topic: {topic_name}

Rules:
- Start with a warm, open-ended question
- Make it easy to answer - not too broad or too narrow
- Be conversational and friendly
- Just ask the question, no preamble"""},
                {"role": "user", "content": f"Start the interview about {topic_name}."}
            ]
            try:
                opening = chat_completion(messages, max_tokens=150)
            except Exception as e:
                print(f"[interviews] Opening generation failed: {e}")
                opening = f"Hi! I'd love to learn more about you. Let's start with {topic_name.lower()}. What's something you'd like to share?"

        # Save opening message
        msg_id = str(uuid.uuid4())
        db.execute(
            text("""INSERT INTO interview_messages 
                (id, session_id, role, content, created_at)
                VALUES (:id, :session_id, :role, :content, :created_at)"""),
            {
                "id": msg_id,
                "session_id": session_id,
                "role": "interviewer",
                "content": opening,
                "created_at": datetime.now(timezone.utc),
            }
        )

        # Update session counts
        db.execute(
            text("""UPDATE interview_sessions 
                   SET questions_asked = 1, messages_count = 1, updated_at = :now
                   WHERE id = :id"""),
            {"id": session_id, "now": datetime.now(timezone.utc)}
        )
        db.commit()

        return InterviewSessionResponse(
            id=session_id,
            twin_id=twin_id,
            topic=topic,
            topic_name=topic_name,
            status="active",
            questions_asked=1,
            messages_count=1,
            items_extracted=0,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )
    finally:
        db.close()


@router.post("/{twin_id}/interviews/{session_id}/message", response_model=InterviewResponse)
async def send_interview_message(
    twin_id: str,
    session_id: str,
    body: InterviewMessage,
    current_user: dict = Depends(get_current_user),
):
    """Send a message in an interview and get a follow-up question."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Get session
        session = db.execute(
            text("""SELECT id, topic, status, questions_asked, messages_count, items_extracted
                    FROM interview_sessions
                    WHERE id = :id AND twin_id = :tid AND user_id = :uid"""),
            {"id": session_id, "tid": twin_id, "uid": user_id}
        ).fetchone()

        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")

        if session[2] != "active":
            raise HTTPException(status_code=400, detail="Interview session is not active")

        topic = session[1]

        # Get twin name
        twin = db.execute(
            text("SELECT name FROM twins WHERE id = :id"),
            {"id": twin_id}
        ).fetchone()
        twin_name = twin[0] if twin else "the person"

        # Save user message
        user_msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        db.execute(
            text("""INSERT INTO interview_messages 
                (id, session_id, role, content, created_at)
                VALUES (:id, :session_id, :role, :content, :created_at)"""),
            {
                "id": user_msg_id,
                "session_id": session_id,
                "role": "interviewee",
                "content": body.message,
                "created_at": now,
            }
        )
        db.commit()

        # Get conversation history
        history = _get_interview_history(db, session_id)

        # Get existing knowledge to avoid repetition
        existing_knowledge = _get_existing_knowledge(db, twin_id)

        # Generate follow-up question
        follow_up = _generate_follow_up(
            twin_name=twin_name,
            topic=topic,
            history=history,
            existing_knowledge=existing_knowledge,
            user_message=body.message,
        )

        # Check if interview should end
        is_complete = False
        if "that's all i needed" in follow_up.lower() or "thank you" in follow_up.lower():
            is_complete = True

        # Save follow-up
        follow_up_msg_id = str(uuid.uuid4())
        db.execute(
            text("""INSERT INTO interview_messages 
                (id, session_id, role, content, created_at)
                VALUES (:id, :session_id, :role, :content, :created_at)"""),
            {
                "id": follow_up_msg_id,
                "session_id": session_id,
                "role": "interviewer",
                "content": follow_up,
                "created_at": datetime.now(timezone.utc),
            }
        )

        # Extract knowledge
        knowledge_items = _extract_knowledge(
            twin_id=twin_id,
            session_id=session_id,
            source_id=session_id,
            user_message=body.message,
            interviewer_response=follow_up,
            topic=topic,
        )

        # Save knowledge items
        if knowledge_items:
            _save_knowledge_items(db, knowledge_items)

        # Update user message with extracted knowledge
        db.execute(
            text("""UPDATE interview_messages 
                   SET knowledge_items_extracted = :items
                   WHERE id = :id"""),
            {"items": json.dumps([{"id": k["id"], "content_type": k["content_type"], "content": k["content"]} for k in knowledge_items]), "id": user_msg_id}
        )

        # Update session counts
        new_questions = session[3] + 1
        new_messages = session[4] + 2  # user + follow-up
        new_items = session[5] + len(knowledge_items)
        new_status = "completed" if is_complete else "active"

        db.execute(
            text("""UPDATE interview_sessions 
                   SET questions_asked = :qa, messages_count = :mc, items_extracted = :ie,
                       status = :status, updated_at = :now
                   WHERE id = :id"""),
            {
                "qa": new_questions,
                "mc": new_messages,
                "ie": new_items,
                "status": new_status,
                "now": datetime.now(timezone.utc),
                "id": session_id,
            }
        )

        # Index interview chunks if complete
        if is_complete:
            all_messages = _get_interview_history(db, session_id)
            all_messages.append({"role": "interviewer", "content": follow_up})
            _index_interview_chunks(user_id, twin_id, session_id, all_messages)

        db.commit()

        return InterviewResponse(
            session_id=session_id,
            message_id=follow_up_msg_id,
            role="interviewer",
            content=follow_up,
            follow_up=follow_up,
            knowledge_extracted=[{"content_type": k["content_type"], "content": k["content"]} for k in knowledge_items],
            questions_asked=new_questions,
            knowledge_count=new_items,
            is_complete=is_complete,
        )
    finally:
        db.close()


@router.get("/{twin_id}/interviews")
def list_interviews(
    twin_id: str,
    current_user: dict = Depends(get_current_user),
    status: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List all interview sessions for a twin."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        query = """
            SELECT id, topic, status, questions_asked, messages_count, items_extracted,
                   created_at, updated_at
            FROM interview_sessions
            WHERE twin_id = :tid AND user_id = :uid
        """
        params = {"tid": twin_id, "uid": user_id, "limit": limit, "offset": offset}

        if status:
            query += " AND status = :status"
            params["status"] = status

        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        rows = db.execute(text(query), params).fetchall()

        # Get total count
        count_query = "SELECT COUNT(*) FROM interview_sessions WHERE twin_id = :tid AND user_id = :uid"
        count_params = {"tid": twin_id, "uid": user_id}
        if status:
            count_query += " AND status = :status"
            count_params["status"] = status
        total = db.execute(text(count_query), count_params).scalar()

        sessions = []
        for r in rows:
            topic_config = INTERVIEW_TOPICS.get(r[1], {})
            sessions.append(InterviewSessionResponse(
                id=str(r[0]),
                twin_id=twin_id,
                topic=r[1],
                topic_name=topic_config.get("name"),
                status=r[2],
                questions_asked=r[3],
                messages_count=r[4],
                items_extracted=r[5],
                created_at=str(r[6]),
                updated_at=str(r[7]),
            ))

        return {"sessions": sessions, "total": total, "limit": limit, "offset": offset}
    finally:
        db.close()


@router.get("/{twin_id}/interviews/{session_id}")
def get_interview(
    twin_id: str,
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get interview session detail with messages."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Get session
        session = db.execute(
            text("""SELECT id, topic, status, questions_asked, messages_count, items_extracted,
                           created_at, updated_at
                    FROM interview_sessions
                    WHERE id = :id AND twin_id = :tid AND user_id = :uid"""),
            {"id": session_id, "tid": twin_id, "uid": user_id}
        ).fetchone()

        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")

        # Get messages
        messages = db.execute(
            text("""SELECT id, role, content, knowledge_items_extracted, created_at
                    FROM interview_messages
                    WHERE session_id = :sid
                    ORDER BY created_at ASC"""),
            {"sid": session_id}
        ).fetchall()

        topic_config = INTERVIEW_TOPICS.get(session[1], {})

        return {
            "id": str(session[0]),
            "twin_id": twin_id,
            "topic": session[1],
            "topic_name": topic_config.get("name"),
            "status": session[2],
            "questions_asked": session[3],
            "messages_count": session[4],
            "items_extracted": session[5],
            "created_at": str(session[6]),
            "updated_at": str(session[7]),
            "messages": [
                {
                    "id": str(m[0]),
                    "role": m[1],
                    "content": m[2],
                    "knowledge_extracted": m[3],
                    "created_at": str(m[4]),
                }
                for m in messages
            ],
        }
    finally:
        db.close()


@router.delete("/{twin_id}/interviews/{session_id}")
def end_interview(
    twin_id: str,
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """End/delete an interview session."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Verify session exists
        session = db.execute(
            text("""SELECT id, status FROM interview_sessions
                    WHERE id = :id AND twin_id = :tid AND user_id = :uid"""),
            {"id": session_id, "tid": twin_id, "uid": user_id}
        ).fetchone()

        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")

        # Index remaining chunks if session was active
        if session[1] == "active":
            all_messages = _get_interview_history(db, session_id)
            if all_messages:
                _index_interview_chunks(user_id, twin_id, session_id, all_messages)

        # Update session status
        db.execute(
            text("""UPDATE interview_sessions 
                   SET status = 'completed', updated_at = :now
                   WHERE id = :id"""),
            {"id": session_id, "now": datetime.now(timezone.utc)}
        )
        db.commit()

        return {"message": "Interview session ended", "id": session_id}
    finally:
        db.close()


@router.get("/{twin_id}/interviews/topics")
def list_topics():
    """List available interview topics."""
    return {
        "topics": [
            {
                "id": key,
                "name": config["name"],
                "description": config["description"],
            }
            for key, config in INTERVIEW_TOPICS.items()
        ]
    }
