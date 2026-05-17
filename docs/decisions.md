# Architecture Decisions

## D-0006 — DB Schema Agreement (2026-05-16)

**Decision:** Use UUID primary keys for all tables (not integer).
**Reason:** UUIDs are portable across environments and safe to expose in APIs.

**Decision:** Use JSONB for persona blob columns.
**Reason:** Persona structure may evolve — JSONB allows flexible schema without migrations.

**Decision:** 9 tables agreed: users, personas, persona_versions, messages,
feedback, preference_pairs, daily_questions_asked, ingestion_jobs, voice_cache.

**Decision:** Indexes on user_id for every table that has it.
Indexes on created_at for messages and feedback (most queried by time).

**Decision:** preference_pairs columns: prompt, chosen, rejected, created_at, user_id.

**Agreed by:** P1, P2, P3, P4 in schema sync call, 2026-05-16.