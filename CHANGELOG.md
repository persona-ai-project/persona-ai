Changelog — Sprint 2 (Days 6–10)
[Day 10] - 2026-05-23
Added

Enhanced GET /healthz — now returns {status, sha, db, qdrant, redis} with real service pings
Returns 200 if all healthy, 503 if any service is down
Lazy redis import to avoid crash on missing module
services/api/ingest/README.md — full parser quirks documentation

PDF OCR limitations, encrypted PDF handling
WhatsApp date format variations (iOS/Android/US locale)
URL JS-heavy sites trafilatura can't extract
Progress states table with progress_pct values
P3 polling pattern with JavaScript example
Common errors and fixes table


REDIS_URL environment variable added to docker-compose.yml

Fixed

import redis moved inside /healthz function to prevent crash-loop when package missing


[Day 9] - 2026-05-22
Verified (End-to-End Tests)

Qdrant: 39 chunks indexed for demo user c1b86221-ff7a-439b-bc6f-11a59bf50175
Semantic search: Score 0.573 returned for "what do I like?" → cricket and biryani content
File upload: queued → parsing → chunking → embedding → indexed all states confirmed in logs
URL ingestion: Wikipedia Cricket page indexed successfully
WhatsApp parser edge cases:

Emoji messages (😊, 🏏, 🍛) — 2 chunks returned, emojis preserved
Short messages ("ok", "👍") — filtered out, only proper content kept
Multi-line messages — joined correctly to previous message


URL edge case: Twitter/X returns 1 chunk gracefully (no crash on JS-heavy sites)

Fixed

time.sleep(0.5) added after each status update in runner.py so P3 can observe progress bar transitions during demos
NLTK punkt and punkt_tab downloaded at module load time via SSL fix


[Day 8] - 2026-05-21
Added

services/api/routers/ingest.py — dedicated ingestion router with 5 routes:

POST /ingest/file — multipart upload, auto-detects type by extension (.pdf/.docx/.md/.txt), uploads to R2, returns 202 + job_id immediately
POST /ingest/social/whatsapp — WhatsApp .txt upload + owner_name form field, uses :: separator to pass owner to runner
POST /ingest/url — JSON body {url, user_id}, validates URL format with regex, no file upload needed
GET /ingest/{job_id} — returns job row with progress_pct (0/25/50/75/100/-1)
DELETE /ingest/source — deletes from Postgres AND calls P1's rag.delete() to remove Qdrant vectors


services/api/routers/__init__.py
Router registered in main.py via app.include_router(ingest_router)
trafilatura==1.12.1 added to requirements.txt
sqlalchemy version bumped to 2.0.36 (2.0.30 no longer available)

Fixed

DELETE route changed from path param to query param to handle R2 keys with / slashes
R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_AUDIO_BUCKET, R2_INGEST_BUCKET, QDRANT_URL, QDRANT_API_KEY referenced via ${VAR} in docker-compose.yml from .env


[Day 7] - 2026-05-20
Added

services/api/ingest/runner.py — full ingestion pipeline with real P1 imports:

from rag.chunker import chunk_text — P1's real NLTK-based chunker (512 words, 20% overlap)
from rag.retriever import index as rag_index — P1's real Qdrant indexer (lazy import to avoid path issues)
State machine: queued → parsing → chunking → embedding → indexed → failed
_parse_file() dispatch to correct parser by source_type
_update_status() — writes each state transition to DB
create_job() — creates QUEUED job row in Postgres
run_ingestion_job() — full async pipeline called via FastAPI BackgroundTasks


NLTK SSL fix + punkt/punkt_tab download at module load
POST /ingest/start returns 202 immediately, pipeline runs in background
GET /ingest/job/{job_id} reads real DB status

Fixed

from services.ai.rag.embedder import Embedder → from rag.embedder import Embedder in P1's retriever.py
shared/ mounted at /app/shared in docker-compose.yml
services/ai/ mounted at /app/services_ai in docker-compose.yml
qdrant-client bumped to 1.11.3 (Prefetch, FusionQuery available from 1.7.0+)
__pycache__ cleared inside Docker to pick up import fixes


[Day 6] - 2026-05-19
Added (P1)

services/ai/parsers/whatsapp.py — WhatsApp chat export parser

Regex handles iOS brackets, Android no-brackets, AM/PM, no leading zeros
Multi-line message joining
System message filtering
owner_name filter — only extracts messages from specified person
Emoji support


services/ai/parsers/pdf.py — PDF parser via pypdf, one chunk per page, skips pages < 50 chars
services/ai/parsers/docx.py — DOCX parser via python-docx
services/ai/parsers/markdown.py — Markdown parser (raw text)
services/ai/parsers/text.py — Plain text parser
services/ai/parsers/url.py — URL parser via trafilatura, never raises on failure
services/ai/tests/test_parsers.py — 17 tests, 0 failures

TestWhatsAppParser: 6 tests
TestMarkdownParser: 5 tests
TestTextParser: 4 tests
TestUrlParser: 2 tests


services/ai/conftest.py — sys.path fix for pytest to find parsers module
services/ai/requirements.txt:

  pypdf==4.2.0
  python-docx==1.1.2
  trafilatura==1.12.1
  python-dateutil==2.9.0
  pydantic==2.7.1
  pytest==8.2.0

Sprint 2 Deliverables — Final Status
DeliverableOwnerStatusAll 5 parsers with unit testsP1✅ Day 6 — 17/17 tests passReal chunker wired into runnerP1 + P2✅ Day 7Real Qdrant indexer wired into runnerP1 + P2✅ Day 7POST /ingest/fileP2✅ Day 8POST /ingest/social/whatsappP2✅ Day 8POST /ingest/urlP2✅ Day 8GET /ingest/{job_id} with progress_pctP2✅ Day 8DELETE /ingest/sourceP2✅ Day 8WhatsApp export → searchable RAG memoryP1 + P2✅ Day 939 chunks in Qdrant, search verifiedP2✅ Day 9Edge cases tested (emoji, short msgs, JS sites)P2✅ Day 9GET /healthz with db/qdrant/redis pingsP2✅ Day 10Ingest README with parser quirksP2✅ Day 10P3 polling shape documentedP2✅ Day 10






## [Sprint 1 - Day 5] - 2026-05-23

### Added
- README.md with full setup guide (clone → env → docker up → migrate → verify)
- Troubleshooting section covering all common errors from Days 1-4
- docker-compose services documentation with ports and env vars
- Makefile with shortcut commands: up, down, restart, migrate, seed, lint, test, build-api, build-web, reset, clean
- scripts/seed_demo_user.py — creates demo user with 30 pre-baked chunks
- Seed verified: demo@persona.ai, Demo Persona, 30 messages, 1 indexed ingestion job

### Sprint 1 Complete ✅
- docker compose up → full stack live in under 90 seconds
- alembic upgrade head → 9 tables in persona DB
- curl localhost:8001/healthz → {"status":"ok"}
- Chunk contract frozen in shared/contracts/chunk.py
- R2 object storage configured with presigned URL support
- Ingestion job state machine: queued→parsing→chunking→embedding→indexed→failed



26f2b5f (changelog: Day 5 complete — Sprint 1 done)
## [Sprint 1 - Day 3 + Day 4] - 2026-05-23

### Added
- Chunk Pydantic v2 model frozen — shared/contracts/chunk.py
- API service in docker-compose (port 8001, hot-reload)
- Web service in docker-compose (port 3002, hot-reload confirmed)
- Cloudflare R2 storage client — storage/client.py
- Presigned URL and upload_bytes methods
- Ingestion job state machine — ingest/runner.py
- States: queued → parsing → chunking → embedding → indexed → failed
- /ingest/presign and /ingest/job endpoints added to API
- R2 credentials added to .env.example

## [Sprint 1 - Day 3] - 2026-05-17

### Added
- Chunk Pydantic v2 model in shared/contracts/chunk.py
- ChunkList wrapper model
- frozen=True for immutability in ingestion pipeline
- API service added to docker-compose with hot-reload
- Web (Next.js) service added to docker-compose on port 3002
- Hot-reload verified for both API and web

### Frozen Contracts
- Chunk: text, source, source_id, created_at, metadata
 main
