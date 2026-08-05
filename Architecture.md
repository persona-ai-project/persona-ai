**PersonaAI**

**18-Day Sprint MVP Plan (May 14 → May 31, 2026)**

_What we build, what we skip, and how we win the demo_

NetSol NIAI Capstone Project | May 2026

> **Timeline note**: the original document was framed as 4 weeks (28 days). The team is delivering the same scope in an 18-day full-time sprint, organised as 4 sprints of 5 / 5 / 4 / 4 days. Per-person day-by-day schedules live in `team/Person1_AI_ML.md`, `team/Person2_Backend.md`, `team/Person3_Frontend.md`, and `team/Person4_Data_Infra.md`. Cross-team decisions are logged in `team/decisions.md`.

# **1. What Is PersonaAI**

PersonaAI is an AI platform that creates a conversational AI twin of a user - not by uploading files or filling forms, but through progressive, interview-style conversations. The system learns who you are over time, builds a structured persona from your answers, and uses that persona to respond as you would when others chat with your twin.

**The Core Loop**

- User answers interview questions → Persona JSON is built and updated
- User chats with their twin → RAG retrieves relevant memories → LLM responds in user's voice
- User gives feedback (👍 / 👎 / rewrite) → System learns preferences → Better responses over time

**Why This Is Not a Basic Chatbot**

- Memory is retrieval-based - the twin actually knows what you told it, not just your last message
- Questions are intelligent - they detect gaps in the persona and ask targeted questions to fill them
- Feedback builds a real dataset - every rewrite is a (chosen, rejected) pair ready for DPO training
- Multi-provider failover - if Groq is down, it silently switches to Cerebras or Gemini
- All free tier - zero cost to run, deployable in one command

# **2. MVP Scope - What We Build vs What We Skip**

Given an 18-day sprint and 4 team members working full-time with AI assistance throughout, here is the honest scope breakdown. **Zero scope cuts** from the original 4-week plan - the work is compressed by parallelism and contract-driven boundaries, not by dropping features.

| **IN SCOPE - 18-day Sprint MVP** | **FUTURE WORK - Phase 2** |
| --- | --- |
| ✅ Progressive onboarding - interview-style persona building<br><br>✅ RAG memory retrieval - twin knows what user told it<br><br>✅ Smart question engine - gap-based, no repeats<br><br>✅ Streaming chat - SSE, multi-provider (Groq → Cerebras → Gemini)<br><br>✅ Feedback system - 👍 👎 + rewrite capturing<br><br>✅ Preference pair dataset - ready for DPO training later<br><br>✅ Persona dashboard - completeness ring, memory breakdown<br><br>✅ Data ingestion - WhatsApp, PDF, DOCX, MD/TXT, URL<br><br>✅ Voice in/out - Groq Whisper STT + Piper TTS<br><br>✅ Public shareable twin page<br><br>✅ Deployed - Vercel + Render free tier<br><br>✅ LLM observability - Langfuse traces on every request<br><br>✅ Eval golden set - 20 (prompt, ideal response) pairs | 🔜 LoRA fine-tuning - architecture designed, pipeline ready<br><br>🔜 DPO training - dataset collecting live during demo<br><br>🔜 Discord / Telegram bots<br><br>🔜 Voice cloning (XTTS-v2)<br><br>🔜 Twitter / LinkedIn archive ingestion<br><br>🔜 Embeddable JS widget (&lt;script&gt; drop-in)<br><br>🔜 Celery scheduled jobs (daily question email)<br><br>🔜 Drift detection (weekly persona re-confirm)<br><br>🔜 A/B evaluation dashboard<br><br>🔜 WhatsApp sandbox (Twilio) |

**Important note on DPO / LoRA:**

The DPO pipeline is NOT being trained in this MVP - but its dataset is being collected live. Every 👎 + rewrite during the demo creates a real preference pair. We show this data in the presentation. Training runs in Phase 2.

**Why LoRA is future work:**

LoRA fine-tuning requires 500+ user-authored messages and GPU time (Kaggle free tier). This is impossible to build and validate inside an 18-day sprint alongside everything else. The architecture is fully designed and shown as a diagram in the presentation.

# **3. Sprint-by-Sprint Plan**

Each person works in parallel. AI tools (Claude, Cursor, ChatGPT, GitHub Copilot) are used throughout for code generation, debugging, and explanation. The goal is to understand what you build - not just paste and run.

The 18 days are split into 4 sprints. Each sprint ends with a clear deliverable that unblocks the next sprint.

| | **Sprint 1 — Foundation**<br>May 14-18 (5 d) | **Sprint 2 — Core**<br>May 19-23 (5 d) | **Sprint 3 — Advanced**<br>May 24-27 (4 d) | **Sprint 4 — Integrate & Demo**<br>May 28-31 (4 d) |
| --- | --- | --- | --- | --- |
| **Person 1 AI / ML** | Qdrant Cloud setup<br><br>FastEmbed + chunker<br><br>RAG dense pipeline | Hybrid search (Qdrant native sparse + RRF)<br><br>`PersonaRetriever` signature freeze (D9) | Question Engine<br><br>`assess_gaps()` + `grade_answer()`<br><br>`QuestionEngine.next_question()` freeze (D11) | Wire RAG into PromptBuilder with P2<br><br>Run eval golden set<br><br>LoRA / DPO slide deck |
| **Person 2 Backend** | FastAPI scaffold<br><br>JWT auth (Supabase)<br><br>Persona CRUD + completeness | Chat endpoint (`sse-starlette`)<br><br>LLM Router (Groq → Cerebras → Gemini)<br><br>SSE format freeze (D9) | Feedback API<br><br>Preference pairs writer<br><br>Feedback payload freeze (D13) | RAG wired into PromptBuilder<br><br>Regenerate endpoint<br><br>Langfuse traces + SSE polish |
| **Person 3 Frontend** | Design system<br><br>Component library<br><br>Onboarding wizard (mocked) | Chat UI + SSE streaming hook<br><br>Markdown render<br><br>"What I remembered" panel | Persona dashboard (completeness ring)<br><br>Feedback UI (👍 👎 ✏️ ⚖️)<br><br>Voice recorder | Public twin page (`/u/[slug]`)<br><br>OpenGraph<br><br>Polish + a11y |
| **Person 4 Infra** | docker-compose<br><br>Postgres + Alembic schema<br><br>Supabase + Upstash<br><br>Chunk model freeze (D3) | Ingestion parsers (WhatsApp, PDF, DOCX, MD, URL)<br><br>Ingestion APIs wired to `index()` | Groq Whisper STT + Piper TTS<br><br>Audio storage<br><br>Voice contract freeze (D13) | Eval golden set runner<br><br>CI/CD — Render + Vercel<br><br>`/healthz` + keep-warm |

# **4. Person 1 - AI / ML Engineer ("The Brain")**

Owns everything that makes the twin intelligent. Two deliverables: a `PersonaRetriever` class (RAG) and a `QuestionEngine` class. Both are standalone Python packages that Person 2's backend calls via function calls.

Full day-by-day schedule with isolation / blocked / blocking flags lives in `team/Person1_AI_ML.md`.

## **4.1 M1.1 - Persona RAG Pipeline (Sprints 1-2)**

Goal: give the twin access to everything the user has ever said, through fast and accurate memory retrieval.

**What you build**

A Python package at `services/ai/rag/` exposing:

- `index(user_id, chunks)` - stores persona chunks in Qdrant
- `search(user_id, query, k=8)` - dense vector search
- `search_hybrid(user_id, query, k=8)` - dense + native BM25 sparse + reciprocal rank fusion via Qdrant's Query API
- `delete(user_id, filter)` - removes chunks by filter
- `stats(user_id)` - returns memory count by source (shown in dashboard)

**Tech stack**

- **Qdrant Cloud free tier — one collection, named vectors `{dense, sparse}`, filtered by `user_id`**: Vector store
- **FastEmbed (`qdrant-client[fastembed]`) with `BAAI/bge-small-en-v1.5` (384 dim, ONNX-quantised, CPU-fast)**: Dense embeddings
- **Qdrant native sparse vectors with BM25 modifier (IDF computed inside Qdrant)**: Sparse / keyword
- **Qdrant Query API `prefetch` + `Fusion.RRF`**: Hybrid fusion (no external `rank_bm25` library)
- **512 tokens with 20% overlap, sentence-boundary aware**: Chunking
- **Recency boost via payload-side score multiplier (chunks from recent weeks rank higher than old ones)**: Recency decay

**Sprint 1 tasks (D1-D5)**

- Day 1: Qdrant Cloud account, API key in `.env`, read FastEmbed + Qdrant hybrid docs (~3 hrs)
- Day 2: `chunker.py` — splits text into 512-token chunks, sentence-aware
- Day 3: Review Chunk Pydantic model with P4 and freeze it in `shared/contracts/chunk.py`
- Day 3-4: `embedder.py` — wraps FastEmbed as a singleton, returns dense + sparse vectors in one call
- Day 4-5: `index()` and `search()` — dense only first, payload includes `user_id`, `source`, `created_at`

**Sprint 2 tasks (D6-D10)**

- Day 6-7: `search_hybrid()` — Qdrant `query_points` with two prefetches (dense + sparse), `Fusion.RRF` server-side
- Day 7: Recency boost as a payload-side scoring formula
- Day 8: Unit tests with 10 sample chunks + 5 queries, recall@5 ≥ 0.8 on a hand-built test set of 20 (query, expected chunk) pairs
- Day 8: Small CLI: `python -m rag index <user_id> <file.jsonl>`
- **Day 9 — Freeze**: `PersonaRetriever.search_hybrid()` Pydantic return type merged in `shared/contracts/retriever.py`

**Acceptance criteria**

- 1,000 chunks index in under 30 seconds on free CPU
- `search_hybrid()` returns results in under 200ms (Qdrant Cloud)
- Hand-built test set of 20 (query, expected chunk) pairs passes recall@5 ≥ 0.8

## **4.2 M1.2 - Intelligent Question Engine (Sprint 3)**

Goal: the system knows what to ask next - not from a hardcoded list, but by analysing what is missing in the persona profile.

**What you build**

A Python package at `services/ai/questions/` exposing:

- `next_question(user_id, context)` - returns the most relevant question to ask right now
- `assess_gaps(persona_json)` - finds empty or low-confidence fields in the persona
- `grade_answer(question, answer)` - LLM judges if an answer is substantive or evasive

**How the next question is chosen**

- Persona gap signals - which fields are empty or low-confidence (e.g. `voice.tone` is missing)
- Recent chat topics - what did the user discuss in the last 48 hours? Go one level deeper
- Drift detection - if a field has not been updated in 30+ days, re-confirm it

The question text itself is generated by Gemini Flash (free) via the **same `openai`-compatible client** Person 2 uses for the chat router, using a structured prompt that takes the gap signals and recent topics as input.

**Sprint 3 tasks (D11-D14)**

- Day 11: Define `GapSignal` taxonomy — every persona field maps to one or more gap types
- Day 11: Implement `assess_gaps()` — pure function, no API calls, fully testable
- Day 11: **Freeze** `QuestionEngine.next_question()` signature in `shared/contracts/questions.py`
- Day 12: Build the question-generation prompt; iterate on it with 10 hand-written examples
- Day 12: Deduplication layer — store asked questions in Postgres, no repeats within 14 days
- Day 13: `grade_answer()` — LLM judges if answer is real or evasive (catches "idk" responses)
- Day 13: 5 hardcoded starter questions for onboarding — must feel curated and natural
- Day 14: 20-question manual review session with the team

**Acceptance criteria**

- Team manually reviews 20 generated questions and rates 17 or more as natural and useful
- No question repeats within 14 days for any test user

## **4.3 Sprint 4 - Integration + Demo Prep (D15-D18)**

- Day 15-16: Connect `PersonaRetriever` to Person 2's backend — P2 calls `search_hybrid()` from the chat endpoint via the frozen contract
- Day 15-16: Connect `QuestionEngine` to Person 2's `/questions/next` endpoint
- Day 16: Test end-to-end - user chats → RAG retrieves correct memory → twin responds accurately
- Day 17: Run the 20-question eval golden set and document recall scores
- Day 17: Prepare LoRA + DPO architecture slides - diagram and explanation for Phase 2 section of presentation
- Day 18: Demo rehearsals (×3), failover drill

**Person 1 note on LoRA / DPO:**

You do NOT need to build LoRA or DPO. You need to be able to explain clearly why they come next, what data they need (500 messages for LoRA, 200 preference pairs for DPO), and show that the preference pair dataset is already being populated by the feedback system. This is a stronger demo argument than a half-working fine-tuning run.

# **5. Person 2 - Backend Engineer ("The Server")**

Owns the entire API layer. Every request from the frontend flows through Person 2's code. Person 1's Python classes are called directly from Person 2's FastAPI routes.

Person 2 also owns the `shared/contracts/` folder — Pydantic models in there are the single source of truth for both the API client (auto-generated TypeScript via `openapi-typescript`) and the Python consumers. Full day-by-day schedule in `team/Person2_Backend.md`.

## **5.1 Sprint 1 — Auth + Persona Profile Service (D1-D5)**

**Tech stack additions**

- **FastAPI** with **Pydantic v2** models
- **Alembic** for Postgres migrations (schema versioned from Day 1)
- **`slowapi`** for per-route rate limiting
- **`sse-starlette`** for streaming responses
- **JWT auth via Supabase**

**What you build**

- `POST /auth/signup`, `POST /auth/login`, `POST /auth/refresh` - JWT auth via Supabase
- `GET/PATCH /persona` - get and update persona JSON
- `GET /persona/completeness` - completeness score (used by Person 3's dashboard ring)
- `GET /persona/history` - version history of persona changes
- `DELETE /me` - wipes all user data from Postgres + Qdrant + storage
- `GET /healthz` - returns build SHA, DB ping status, Qdrant ping status (used by Render keep-warm)

**Persona completeness scoring**

Each section of the persona JSON has a weight. Completeness = weighted average of filled, high-confidence fields:

- `voice` - 25% weight (most important - defines the twin's character)
- `opinions` - 20% weight
- `topics` - 15% weight
- `quirks` - 15% weight
- `identity` - 10% weight
- `knowledge_anchors` - 10% weight
- `boundaries` - 5% weight

**Day 5 — Freeze**: `/persona/completeness` response Pydantic model in `shared/contracts/persona.py`. P3 stops mocking the ring from this day onward.

## **5.2 Sprint 2 — Chat Endpoint + LLM Router (D6-D10)**

This is the most important module. Every chat request flows through here.

**Request flow inside a single chat message**

- Auth + `slowapi` rate-limit check
- Load last 20 messages of conversation history
- `PromptBuilder` - combine persona JSON + RAG chunks (from Person 1, stubbed until Day 15) + history into final prompt
- `LLMRouter` - try Groq, fallback to Cerebras, fallback to Gemini, fallback to HuggingFace
- `EventSourceResponse` (sse-starlette) streams tokens back to frontend + logs trace to Langfuse + stores assistant message

**LLM Router design (thesis-worthy artifact)**

- One `openai.AsyncOpenAI` client per provider, instantiated with that provider's `base_url` and `api_key` (Groq, Cerebras, and Gemini all expose OpenAI-compatible endpoints — one client class, three configurations)
- Tracks each provider's latency and remaining quota in **Upstash Redis** (keys: `quota:{provider}:rpm`, `quota:{provider}:rpd`, `latency:{provider}:p50`)
- Circuit breaker trips for 60 seconds on rate limit, 10 seconds on other errors
- Provider ordering = lowest recent latency + highest remaining quota

**Day 9 — Freeze**: SSE event format (event names + data shape) merged in `shared/contracts/chat_sse.py`. P3 stops mocking the stream from this day onward.

## **5.3 Sprint 3 — Feedback + Learning Loop (D11-D14)**

**What you build**

- `POST /feedback` - accepts `thumbs_up`, `thumbs_down`, `rewrite`, `side_by_side` feedback types
- `GET /feedback/stats` - aggregate counts for the dashboard
- `POST /questions/{id}/answer` - stores user's answer and triggers persona update
- `GET /questions/next` - calls Person 1's `QuestionEngine.next_question()`

**Preference pair creation (most important feedback flow)**

When a user submits a rewrite: the AI's original response becomes `rejected`, the user's rewrite becomes `chosen`. This `(chosen, rejected)` pair is stored directly in the `preference_pairs` table - ready for DPO training when enough pairs accumulate.

**Day 13 — Freeze**: `/feedback` payload schema in `shared/contracts/feedback.py`. P3 (feedback UI) and P1 (`grade_answer`) consume this.

## **5.4 Sprint 4 — RAG Integration + Polish (D15-D18)**

- Day 15: Wire `search_hybrid()` from Person 1 into `PromptBuilder` (replace the stub)
- Day 15: Return RAG metadata (top 5 retrieved chunks) in the chat response - Person 3 shows this in the "What I remembered" panel
- Day 16: Add `/chat/{id}/regenerate` endpoint
- Day 16: Add Langfuse trace to every chat request (inputs, retrieved chunks, provider used, tokens, latency)
- Day 17: SSE streaming polish - handle client disconnect, partial responses
- Day 17-18: Failover drills with P4 (kill Groq key, confirm Cerebras takes over within 1s)

# **6. Person 3 - Frontend Engineer ("The Experience")**

If the frontend is beautiful and fluid, the whole project looks good - even if the backend has rough edges. Person 3 owns everything the examiner sees and touches during the demo.

**Stack additions**

- **Next.js 14 (App Router)** with React Server Components where possible
- **TanStack Query v5** for non-SSE fetches (persona, dashboard, feedback stats, ingestion status)
- **`openapi-typescript`** generates the API client from Person 2's OpenAPI schema — no hand-typed contracts
- **Tailwind CSS + shadcn/ui** primitives, customised with the dark-purple theme
- **Framer Motion** for transitions

Full day-by-day schedule in `team/Person3_Frontend.md`.

## **6.1 Sprint 1 — Design System + Onboarding Wizard (D1-D5)**

**Design system (build this first, everything else uses it)**

- Dark-first theme with warm purple accent (`#8b5cf6`)
- Components: Button, Card, Input, Textarea, Dialog, Avatar, Badge, Progress, Toaster
- Framer Motion variants for all transitions - 200ms ease-out entrances
- Skeleton loading states everywhere - no spinners

**Onboarding wizard (`/onboarding`)**

- Full-screen single-question-at-a-time layout
- 5 starter questions from Person 1's `QuestionEngine` (mocked Day 1-10, real from Day 11)
- Each card has: text input + microphone button (voice → Groq Whisper → text via Person 4, mocked Day 1-12)
- Progress dots at top: ● ● ○ ○ ○
- Final screen shows first persona trading card - avatar + key voice traits + "Meet your twin" CTA

P3 builds this entire flow against mock JSON in Sprint 1 — zero dependency on the backend until Day 9.

## **6.2 Sprint 2 — Twin Chat Interface (D6-D10)**

**Layout**

- Left rail - conversation list (collapses on mobile)
- Center - messages with streaming tokens, markdown, code highlighting
- Right rail (collapsible) - "What I remembered" panel showing top-5 RAG chunks with relevance scores

**Message features**

- Streaming tokens via the `useEventSource` hook bound to `shared/contracts/chat_sse.py` types
- Inline feedback row under every assistant message: 👍 👎 ✏️ Rewrite ⚖️ Compare
- Rewrite flow - clicking ✏️ opens inline textarea with original response as placeholder
- Compare flow - clicking ⚖️ generates two candidates side-by-side, user picks better one
- Regenerate - calls `/chat/{id}/regenerate`

P3 builds the SSE hook against a hand-written mock stream until Day 9, then swaps to the real endpoint after P2's freeze.

## **6.3 Sprint 3 — Persona Dashboard + Feedback UI (D11-D14)**

**Dashboard (`/dashboard`)**

- Completeness ring - animated SVG showing percentage, counts up on load
- Persona card grid - each section of persona JSON shown as an editable card
- Memory inventory - bar chart showing chunks indexed by source (chat, WhatsApp, docs)
- Question of the day - sticky card that lets user answer inline
- Feedback stats - "X rewrites this week, Y preference pairs collected"

**Feedback UI in chat**

- 👍 / 👎 is optimistic - appears instantly, no loading state (TanStack Query mutation rollback on error)
- Rewrite textarea - submits to `POST /feedback` with `kind=rewrite`
- Side-by-side comparison - submits to `POST /feedback` with `kind=side_by_side`

**Voice recorder**

- Records 10-30s audio via MediaRecorder API, POSTs to `/voice/transcribe`
- Built against mock until P4's Day 13 freeze, real after

## **6.4 Sprint 4 — Public Twin Page + Polish (D15-D18)**

- Day 15-16: Public page (`/u/[slug]`) - shareable link, no sign-up required
- Stripped chat UI - no left rail, no rewrite, just chat with the twin
- Rate-limit toasts - "X more messages this hour"
- Day 16: Sharing settings in dashboard - toggle on/off, copy link, slug editor
- Day 16: OpenGraph metadata - twin name + avatar preview when pasted in WhatsApp/Slack
- Day 17-18: Polish, a11y pass, mobile responsiveness, demo rehearsal

# **7. Person 4 - Data & Infrastructure Engineer ("The Foundation")**

**Nothing else can start until Person 4 ships the local dev environment by end of Day 3.** Person 4 also owns data ingestion, voice pipeline, eval framework, deployment, and serves as **Release Coordinator** (runs standup, owns CI/CD).

Full day-by-day schedule in `team/Person4_Data_Infra.md`.

## **7.1 Sprint 1 — Docker + DB + Schema Freeze (MUST SHIP BY END OF DAY 3)**

**docker-compose.yml services**

- `postgres` - with persistent volume
- `qdrant` - local vector store for dev (mirrors Qdrant Cloud schema)
- `redis` - for rate limiting and provider quota tracking
- `api` - Person 2's FastAPI (hot-reload via uvicorn `--reload`)
- `web` - Person 3's Next.js
- `langfuse` - local observability

**Database schema (shared with all, managed via Alembic)**

- `users` - id, email, created_at
- `personas` - user_id, json_data, version, updated_at
- `persona_versions` - full version history
- `conversations` + `messages` - chat history
- `feedback` - message_id, kind, payload, created_at
- `preference_pairs` - prompt, chosen, rejected, weight, source
- `daily_questions_asked` - user_id, question_hash, asked_at
- `ingestion_jobs` - id, user_id, source, status, progress
- `voice_cache` - sha256(text + voice_id) → object_storage_url

**Day 3 — Freeze**: `Chunk` Pydantic model in `shared/contracts/chunk.py` (P1 consumes it for `index()`, P4 produces it from every parser).

**Deployment targets (all free)**

- Frontend - Vercel (auto-deploys on git push)
- API - Render free tier (Docker-based)
- Database - Supabase free tier (500MB, Postgres + Auth + Storage)
- Vectors - Qdrant Cloud free tier (1GB)
- Redis - Upstash free tier
- Storage - Supabase Storage (audio + uploads)

## **7.2 Sprint 2 — Data Ingestion Pipelines (D6-D10)**

Each ingestion goes: upload → parse → normalise → filter (user-authored only) → chunk → embed → index into Qdrant via Person 1's `index()` method.

**Parsers to build**

- WhatsApp `.txt` export - multiline message aware, strips system messages, owner-only filter
- PDF - `pypdf` text extraction
- DOCX - `python-docx`
- Markdown / TXT - direct read
- URL - `trafilatura` for main content extraction

**API endpoints**

- `POST /ingest/file` - PDF, DOCX, MD, TXT
- `POST /ingest/social/whatsapp` - `.txt` export
- `POST /ingest/url` - fetch and extract
- `GET /ingest/{id}` - status with progress (polled by P3 dashboard)
- `DELETE /ingest/source/{source}` - wipe all chunks from one source

## **7.3 Sprint 3 — Voice Pipeline (D11-D14)**

**Speech to text (STT) — Groq Whisper only**

- **Groq Whisper Large v3 Turbo** for ALL audio (free tier: 2,000 req/day, 8 hrs audio/day, 25 MB cap — well within demo needs)
- `faster-whisper` retained ONLY as an offline dev-mode fallback, not in production
- `POST /voice/transcribe` - returns `{ text, audio_id, duration_s }`

**Text to speech (TTS)**

- **Piper TTS** - ONNX-based, fast on CPU, 3-5 default voices
- `POST /voice/tts` - returns audio URL
- Cache all TTS output by `sha256(text + voice_id)` in the `voice_cache` table → Supabase Storage URL - never re-synthesise same text
- `GET /voice/voices` - list available voices

**Day 13 — Freeze**: `/voice/transcribe` response schema in `shared/contracts/voice.py`. P3's VoiceRecorder consumes it.

## **7.4 Sprint 4 — Evaluation + Deploy (D15-D18)**

**Eval golden set**

- Team builds 20 (prompt, ideal response, expected persona traits) tuples together on Day 15
- Stored as JSONL in `eval/golden/`
- Eval runner measures: persona match, style similarity, latency
- One-command run: `python eval/runner.py` - output is a markdown report

**CI/CD**

- GitHub Actions - `ci.yml` runs lint (ruff, mypy) + tests on every PR
- `deploy-api.yml` - Docker build + Render deploy on push to `main`
- `deploy-web.yml` - implicit via Vercel git integration
- `keep-warm.yml` - cron every 10 min hitting `/healthz` to prevent Render free-tier sleep
- `db-backup.yml` - nightly Postgres dump

**Deploy day (Day 16-17)**

- Day 16 AM: First deploy of API to Render, web to Vercel from `main`
- Day 16 PM: Smoke test all flows on prod URLs
- Day 17: `keep-warm.yml` active, failover drill with P2

# **8. Demo Day Script (5 Minutes)**

This is exactly what you show during the NetSol presentation. Practice this sequence until it runs smoothly (3 rehearsals: May 30 evening, May 31 AM, May 31 PM before stage).

- **Sign up + onboarding wizard** (P3 + P4 spotlight)
  - Open fresh browser, sign up with a new account
  - Complete 5 onboarding questions using voice input (shows Groq Whisper STT)
  - Final screen shows the persona trading card with voice traits filled in

- **Chat with the twin + RAG memory demo** (P1 + P2 spotlight)
  - Ask the twin something the user mentioned during onboarding
  - Show the "What I remembered" right panel - top 5 RAG chunks with relevance scores
  - This proves RAG is working - the twin knows because it retrieved that memory

- **Feedback + preference dataset** (P2 + P3 spotlight)
  - Click 👎 on a response, then click "Rewrite as me" and type a better version
  - Open the database / dashboard and show that a new preference pair was just created
  - Say: "This pair will be used to train DPO when we have enough. We already have X pairs."

- **Persona dashboard** (P3 spotlight)
  - Open dashboard - show completeness ring (e.g. 62%)
  - Show memory breakdown chart - "X chunks from chat, Y from WhatsApp"
  - Answer one daily question inline - ring ticks up

- **Shareable public twin** (P3 spotlight)
  - Toggle "Make my twin shareable" in dashboard
  - Copy public link, open in incognito window
  - Chat with the twin as a stranger - show it works without login

- **Phase 2 slide - LoRA + DPO** (P1 spotlight)
  - Show the architecture diagram: Supervised Fine-Tuning → BERT Reward Model → PPO
  - Show the `preference_pairs` table with real data collected during the demo
  - Say: "With 500 messages for LoRA and 200 pairs for DPO, we run Phase 2 training"
  - Show W&B training curve mockup or explain what it would look like

- **Failover drill** (P2 + P4 spotlight, optional showpiece)
  - One team member kills the Groq API key mid-demo
  - Chat still responds within 1s from Cerebras
  - Open Langfuse trace to show the provider switch

# **9. Integration Contracts — Freeze Schedule**

These are the shared interfaces. Once frozen, both sides can work independently without breaking each other. **Each contract lives as a Pydantic model in `shared/contracts/` (owned by P2's repo folder). Freezing a contract = merging the PR; the TypeScript client regenerates automatically via `openapi-typescript`.**

| **Contract** | **Owner** | **Frozen by EOD** | **Consumers** |
| --- | --- | --- | --- |
| `Chunk` Pydantic model | P4 | Day 3 (Sat May 16) | P1 (`index()` input), P4 (parser output) |
| `/persona/completeness` response | P2 | Day 5 (Mon May 18) | P3 (dashboard ring) |
| `PersonaRetriever.search_hybrid()` | P1 | Day 9 (Fri May 22) | P2 (PromptBuilder) |
| POST `/chat` SSE event format | P2 | Day 9 (Fri May 22) | P3 (streaming hook) |
| `QuestionEngine.next_question()` | P1 | Day 11 (Sun May 24) | P2 (`/questions/next`), P3 (onboarding wizard) |
| POST `/feedback` payload schema | P2 | Day 13 (Tue May 26) | P3 (feedback UI), P1 (`grade_answer`) |
| POST `/voice/transcribe` response | P4 | Day 13 (Tue May 26) | P3 (VoiceRecorder) |

**Rule**: outside of a contract-freeze checkpoint, **nobody waits on anybody**. Everyone builds against mocks of the not-yet-frozen contracts.

# **10. Why PersonaAI Is Not Basic**

**The core argument:**

A basic chatbot has a system prompt. PersonaAI has a living, structured persona that grows with every conversation, retrieves the right memories at the right time, actively interviews the user to fill its own gaps, and collects training data from every interaction to improve itself over time.

## **What makes each component non-trivial**

- **RAG is not just context stuffing**: The retriever uses hybrid dense + native sparse (BM25) search with reciprocal rank fusion inside Qdrant's Query API, plus recency decay. The twin does not just prepend your profile to every message - it retrieves the 8 most relevant memories for each specific question.
- **Question engine is not a form**: It analyses the persona JSON to find gaps, checks what the user has been talking about recently, avoids repeating questions within 14 days, and generates natural-sounding interview questions using an LLM - not a dropdown menu.
- **Feedback is not just a rating**: Every 👎 + rewrite creates a `(chosen, rejected)` pair stored in a structured format ready for DPO training. This is real RLHF data collection, not just a star rating that goes nowhere.
- **LLM router is not just one API call**: A single OpenAI-compatible client class is configured for three providers; circuit breaker, provider health tracking in Redis, and automatic failover from Groq to Cerebras to Gemini is a production-grade multi-provider orchestration system.
- **LoRA + DPO are not magic words**: We can explain exactly what they do. LoRA adapts the base model's weights using the user's own writing style. DPO uses the preference pairs collected during normal usage to train the model to prefer responses more like the user. The data is already being collected. The training runs in Phase 2.

# **11. Complete Free-Tier Stack**

Every service used in this project has a free tier sufficient for development and demo.

| **Service** | **Provider** | **Free limit** |
| --- | --- | --- |
| Frontend hosting | Vercel | Unlimited deploys, free subdomain |
| API hosting | Render | Free Docker hosting, sleeps after inactivity (mitigated by `/healthz` + `keep-warm.yml`) |
| Database (Postgres) | Supabase | 500MB, 2 projects |
| Vector store | Qdrant Cloud | 1GB forever free |
| Cache / rate limit | Upstash Redis | 10,000 requests/day |
| Object storage | Supabase Storage | 1GB free |
| LLM - primary | Groq API | Free tier, very fast (Llama 3.1) — OpenAI-compatible endpoint |
| LLM - fallback 1 | Cerebras API | Free tier — OpenAI-compatible endpoint |
| LLM - fallback 2 | Gemini Flash | Free tier, 1M tokens/day — OpenAI-compatible endpoint |
| LLM - question gen | Gemini Flash | Same free quota |
| STT (all audio) | Groq Whisper Large v3 Turbo | 2,000 req/day, 8 hrs audio/day, 25 MB file cap |
| STT (dev fallback) | faster-whisper | Self-hosted, CPU, free (offline-only) |
| TTS | Piper TTS | Self-hosted, ONNX, free |
| Observability | Langfuse | Self-hosted on Render, free |
| Training GPU | Kaggle | 30 hrs/week P100 GPU (Phase 2) |
| Training tracking | Weights & Biases | Personal free tier |

# **12. End-of-Sprint-4 Definition of Done**

By May 31 at presentation time, the team must be able to demonstrate the following live:

- Fresh browser → sign up → onboarding with voice → persona trading card appears
- Chat with twin → ask about something said during onboarding → RAG retrieves it, right panel shows proof
- Click 👎 → rewrite response → show new row in `preference_pairs` table in DB
- Open dashboard → completeness ring at 60%+ → answer one daily question → ring ticks up
- Toggle shareable → copy public link → open in incognito → chat as stranger → rate-limit toast
- Show Langfuse dashboard → every chat request has a trace with retrieval inputs and latency
- Show Phase 2 architecture slide → LoRA pipeline → DPO pipeline → `preference_pairs` count
- One team member kills the Groq API key mid-demo → chat still responds from Cerebras within 1s

**The bar:**

If all 8 of these work on demo day, PersonaAI is a strong, well-scoped capstone project that clearly demonstrates RAG, intelligent questioning, multi-provider LLM orchestration, feedback-driven learning, and a real path to fine-tuning - all on a zero-cost stack. That is more than enough.

# **13. Risk Register**

Eight named risks with named owners and pre-baked mitigations. Reviewed at every Day-13 and Day-16 standup.

| # | Risk | Owner | Mitigation |
| --- | --- | --- | --- |
| 1 | Render free tier cold-starts kill demo | P4 | `/healthz` endpoint + `keep-warm.yml` cron (every 10 min) from Day 16 |
| 2 | Qdrant Cloud free quota hit during ingestion stress test | P1 + P4 | One collection, payload index on `user_id`, 1 dev user during build, prod ingestion gated to < 100 MB total |
| 3 | LLM provider goes down mid-demo | P2 | Circuit breaker + 3-provider failover proven in rehearsal #1 (Day 17) |
| 4 | SSE event format changes after Day 9 freeze | P2 + P3 | TS types regenerated from OpenAPI in CI; format change requires consumer-side PR review |
| 5 | Persona JSON shape drifts between P1, P2, P3 | P2 + P1 | Single Pydantic model in `shared/contracts/persona.py`, Alembic-migrated, versioned in `persona_versions` |
| 6 | Voice transcribe latency > 3s on demo Wi-Fi | P4 | Groq Whisper measured < 1s for 10s clips; local `faster-whisper` standby on demo laptop |
| 7 | One teammate falls sick mid-sprint | All | Cross-pair touchpoints documented (P1↔P2 share `PersonaRetriever`, P3↔P4 share voice + ingestion). Any pair can cover one absence for 1-2 days. |
| 8 | Demo venue internet fails | P4 | Pre-recorded backup video + `localhost` Docker compose ready on a laptop with mobile hotspot |

# **14. Definition of Daily Done**

Sprint mode requires daily forward motion. The rules:

- **Every workday, each person merges at least one PR.** If a person does not, it is the first thing addressed in the next morning's standup — the team identifies the unblock together.
- **09:00 standup, 10 minutes, async in Discord/Slack.** Three lines each: *yesterday / today / blocked-on*. P4 (Release Coordinator) pings anyone who has not posted by 09:30.
- **PR rule for `shared/contracts/`**: requires 1 review from the consumer side (e.g. P3 reviews a P2 contract PR for `/feedback`). Domain code merges with self-approval to keep velocity.
- **Contract-freeze days are non-negotiable**: missing a freeze on Day 3, 5, 9, 11, or 13 blocks the whole team. If a freeze is at risk, raise it at the morning standup that day so the team can pair on it.
- **No new features after Day 14.** Sprint 4 (Day 15-18) is integration, deploy, eval, and rehearsal only.
- **All integration disputes are recorded in `team/decisions.md`** with date, parties involved, and final call. Flat team means written-down decisions are how we stop re-litigating.

The single sentence to memorise:

> **Solo by default. Collaborate only at contract-freeze checkpoints. Ship one PR a day.**
