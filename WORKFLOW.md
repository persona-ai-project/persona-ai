# Persona AI — Team Workflow Guide

---

## Team Roles

| Person | Role | Owns |
|---|---|---|
| **P1 — AI/ML** | AI pipeline, RAG, chunking, embeddings, prompts, Langfuse traces | `services/ai/`, `shared/contracts/`, parsers, chunker.py, embedder.py |
| **P2 — Backend** | API endpoints, DB schema, migrations, business logic | `services/api/`, `shared/prisma/` |
| **P3 — Frontend** | UI, Next.js pages, components, API integration | `apps/web/` |
| **P4 — Data/Infra** | Docker, CI/CD, DB infra, vector DB, cloud services | `infra/`, `scripts/`, `.github/`, `docker-compose.yml`, root config |

> **Rule:** You can read anyone's folder but only modify your own. Cross-folder changes need a discussion first.

---

## Current Infrastructure (Day 3 Complete ✅)

All services run locally via Docker. After cloning and running `docker compose up -d`:

| Service | URL | Purpose |
|---|---|---|
| Langfuse | http://localhost:3001 | AI observability & tracing dashboard |
| Web (Next.js) | http://localhost:3002 | Frontend app |
| API (FastAPI) | http://localhost:8001 | Backend API |
| Postgres | localhost:5432 | Primary database |
| Redis | localhost:6379 | Caching & queues |
| Qdrant | http://localhost:6333 | Vector database for embeddings |
| MinIO | http://localhost:9001 | S3-compatible file storage |
| ClickHouse | localhost:8123 | Analytics database (used by Langfuse) |

> **Hot-reload note:** Web hot-reload works inside Docker on Windows via webpack polling (configured in `next.config.js`). Edit any file in `apps/web/` and the browser updates automatically within 1-2 seconds.

---

## Repository Folder Structure

```
persona-ai/
│
├── apps/                        ← P3 (Frontend)
│   └── web/                       Next.js app — pages, components, styles
│       ├── app/
│       │   ├── page.tsx           Home page
│       │   └── layout.tsx         Root layout
│       ├── Dockerfile
│       ├── .dockerignore          Excludes node_modules from Docker build
│       ├── next.config.js         Webpack polling config for hot-reload in Docker
│       ├── package.json
│       └── tsconfig.json
│
├── services/                    ← P2 (Backend) + P1 (AI/ML)
│   ├── api/                       FastAPI endpoints, controllers, middleware (P2)
│   │   ├── db/
│   │   │   ├── models/
│   │   │   │   ├── base.py
│   │   │   │   └── models.py      All 9 table definitions
│   │   │   └── migrations/
│   │   │       └── versions/
│   │   │           └── 0001_initial.py
│   │   ├── main.py                API entrypoint with auto-migration
│   │   ├── alembic.ini
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── ai/                        AI pipeline — RAG, chunker, embedder (P1)
│
├── shared/                      ← P1 (AI/ML) contracts + P2 (Backend) prisma
│   ├── contracts/                 Frozen Pydantic models shared across services
│   │   ├── __init__.py
│   │   └── chunk.py               Chunk model (frozen=True, immutable)
│   ├── utils/                     Shared utility functions
│   └── prisma/                    DB schema (if using Prisma alongside Alembic)
│
├── infra/                       ← P4 (Data/Infra)
│   ├── docker/                    Additional Docker configs
│   └── ci/                        GitHub Actions workflow files
│
├── scripts/                     ← P4 (Data/Infra)
│   └── seed.py                    DB seed scripts, setup helpers
│
├── docs/                        ← Everyone
│   ├── architecture.md            System design (P4 writes)
│   ├── api.md                     API reference (P2 writes)
│   ├── ai.md                      AI/prompt docs (P1 writes)
│   ├── frontend.md                UI component docs (P3 writes)
│   └── decisions.md               Architecture decisions log (everyone)
│
├── .github/                     ← P4 (Data/Infra)
│   └── workflows/
│       └── ci.yml
│
├── clickhouse-config.xml        ← P4 only — do not modify without discussion
├── docker-compose.yml           ← P4 only — do not modify without discussion
├── .env.example                 ← P4 — add variable names here (no real values)
├── .env                         ← NEVER commit — each person fills their own
├── .gitignore                   ← P4
├── CHANGELOG.md                 ← Everyone updates each sprint
├── WORKFLOW.md                  ← This file
├── README.md                    ← P4
└── LICENSE
```

---

## ⚡ Complete Team Git Flow — How Every Commit Gets to Main

This is the **single rule everyone follows.** No exceptions.

```
Your machine
    │
    ▼
feature/your-branch   ← you work here
    │
    │  git push origin feature/your-branch
    ▼
GitHub (feature branch)
    │
    │  Open PR → target: changelog
    ▼
changelog branch      ← P4 reviews + merges here
    │
    │  P4 updates CHANGELOG.md with what shipped
    │  git push origin changelog
    ▼
GitHub (changelog branch)
    │
    │  Open PR → target: main
    │  Requires 1 approval
    ▼
main branch           ← stable, production-ready
```

### Step by step for every team member:

**Step 1 — Start your work:**
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

**Step 2 — Work and commit often:**
```bash
git add .
git commit -m "feat: what you built"
```

**Step 3 — Push your branch:**
```bash
git push origin feature/your-feature-name
```

**Step 4 — Open PR targeting `changelog` (NOT main):**
- Go to GitHub → Pull Requests → New PR
- Base: **`changelog`** ← Compare: `feature/your-feature-name`
- Write a clear title and description
- Tag P4 as reviewer

**Step 5 — P4 reviews and merges to `changelog`:**
- P4 checks: does it work? right folder? breaks anything?
- P4 merges the PR into `changelog`

**Step 6 — P4 updates CHANGELOG.md:**
```bash
git checkout changelog
git pull origin changelog
```
P4 opens `CHANGELOG.md` and adds entry at the top:
```markdown
## [Sprint X - Day Y] - YYYY-MM-DD

### Added
- What was added

### Fixed
- What was fixed
```
Then:
```bash
git add CHANGELOG.md
git commit -m "changelog: describe what shipped"
git push origin changelog
```

**Step 7 — Open PR from `changelog` → `main`:**
- Go to GitHub → Pull Requests → New PR
- Base: **`main`** ← Compare: `changelog`
- Title: what sprint/day this covers
- Requires 1 approval before merge
- After approval → merge to `main`

**Step 8 — Clean up your local branch:**
```bash
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

---

## Branch Structure

```
main                  → stable, production-ready, no direct pushes EVER
└── changelog         → everything passes through here before main
    └── feature/*     → your daily working branches
    └── fix/*         → bug fixes
    └── chore/*       → config, tooling, non-feature work
    └── docs/*        → documentation only changes
```

### Hard Rules
- **NEVER push directly to `main`** — not even P4
- **NEVER push directly to `changelog`** — always via feature PR
- **Every feature branch → PR → `changelog` → PR → `main`**
- `main` requires **1 approval** before merge
- Keep feature branches short-lived — PR within 2 days of starting

---

## Sprint Progress — What's Done and What's Next

### ✅ Day 1 — Foundation Setup (Complete)
**Date:** Thu May 14
**Led by:** P4 (Data/Infra)
**Blocking:** Everyone was blocked until this was done

**What was completed:**
- Docker Compose with all 8 services: Postgres, Redis, Qdrant, Langfuse, MinIO, ClickHouse, API, Web
- ClickHouse single-node Keeper config (no ZooKeeper needed)
- Google OAuth for Langfuse login
- GitHub repo setup with branch protection on `main`
- Full folder structure with `.gitkeep` placeholders
- `.env.example` with all variable names documented
- `WORKFLOW.md` created
- GitHub Actions CI skeleton

**Who was unblocked after Day 1:**
- ✅ P2 (Backend) — could start DB schema work
- ✅ P3 (Frontend) — could start Next.js setup
- ✅ P1 (AI/ML) — could start RAG pipeline planning

---

### ✅ Day 2 — DB Schema + Alembic Migration (Complete)
**Date:** Fri May 15
**Led by:** P2 (Backend)
**Blocking:** P2's work was blocking P4 (Data/Infra) who needed the DB tables to wire the embedder pipeline

**What was completed:**
- 30-min all-hands DB schema sync — all 4 people agreed on 9 tables
- All 9 tables written with Alembic migration `0001_initial`:
  - `users`, `personas`, `persona_versions`, `messages`
  - `feedback`, `preference_pairs`, `daily_questions_asked`
  - `ingestion_jobs`, `voice_cache`
- UUID primary keys on all tables
- JSONB for persona blob columns
- Indexes: `user_id` on every table, `created_at` on messages + feedback
- `alembic upgrade head` auto-runs on API container start
- FastAPI server running on port `8001` with `/healthz` and `/docs`
- Architecture decision D-0006 logged in `docs/decisions.md`
- Separate `persona` database created (separate from Langfuse's `app` DB)

**Who was unblocked after Day 2:**
- ✅ P4 (Data/Infra) — DB tables confirmed, can now wire embedder.py and ingestion pipeline
- ✅ P1 (AI/ML) — can now design RAG queries against real table structure
- ✅ P3 (Frontend) — can now plan UI flows knowing what data exists

---

### ✅ Day 3 — Chunk Contract Freeze + API/Web in Compose (Complete)
**Date:** Sat May 16 – Mon May 19
**Led by:** P1 (AI/ML) wrote contract, P4 (Data/Infra) wired Docker
**Blocking:** P1's Chunk contract was blocking P4 (Data/Infra) who needed the frozen model to start `embedder.py`

**What was completed:**
- 15-min sync: P1 and P4 agreed on Chunk model fields
- `shared/contracts/chunk.py` written with Pydantic v2:
  - Fields: `text: str`, `source: str`, `source_id: str`, `created_at: datetime`, `metadata: dict`
  - `frozen=True` — immutable after creation (safe for ingestion pipeline)
- `ChunkList` wrapper model added
- Immutability verified — mutating a chunk raises `frozen_instance` error
- `api` service added to `docker-compose.yml` (port 8001, hot-reload via RELOAD=true)
- `web` service added to `docker-compose.yml` (port 3002)
- Web hot-reload working inside Docker on Windows via webpack polling in `next.config.js`
- Named volume `web_node_modules` used to preserve node_modules inside Docker
- `.dockerignore` added to prevent local `node_modules` overwriting Docker image
- Chunk contract announced as frozen ✅

**Who was unblocked after Day 3:**
- ✅ P4 (Data/Infra) — can now start `embedder.py` using the frozen Chunk model
- ✅ P2 (Backend) — can now write API endpoints that accept/return Chunk objects
- ✅ P3 (Frontend) — web service running in Docker with hot-reload confirmed working

---

## What Each Person Works On Next

### P1 — AI/ML
```
Next tasks:
- Write services/ai/chunker.py — splits documents into Chunk objects
- Write services/ai/parser.py — parse PDF/text into raw text
- Log chunking pipeline to Langfuse
- Connect chunker output to embedder
```

### P2 — Backend
```
Next tasks:
- Write API endpoints: POST /persona, GET /persona/:id
- Write POST /ingest endpoint that triggers ingestion_jobs
- Connect endpoints to DB using SQLAlchemy models
- Return Chunk objects from relevant endpoints
```

### P3 — Frontend
```
Next tasks:
- Create persona creation UI page in apps/web/app/
- Connect to API endpoints
- Show ingestion status from ingestion_jobs table
- Hot-reload is working — edit files and browser updates automatically
```

### P4 — Data/Infra
```
Next tasks (now unblocked after Day 3):
- Write services/ai/embedder.py using frozen Chunk model
- Connect embedder to Qdrant for vector storage
- Wire ingestion pipeline: parser → chunker → embedder → Qdrant
- Add Qdrant collection setup script in scripts/
- Review and merge all incoming PRs to changelog
```

---

## Blocking Dependencies (Who Waits for Who)

```
Day 1 — P4 (Infra) sets up Docker
    └── Unblocks: P1, P2, P3 (everyone)

Day 2 — P2 (Backend) writes DB schema
    └── Unblocks: P4 (can wire embedder pipeline to real tables)
                  P1 (can design RAG queries)
                  P3 (knows what data exists)

Day 3 — P1 (AI/ML) freezes Chunk contract
    └── Unblocks: P4 (can write embedder.py)
                  P2 (can write endpoints that return Chunks)
                  P3 (knows what data shape to expect from API)
```

> **Rule:** If your work is blocking someone, it is highest priority that day.

---

## Feature Workflow — Build Order by Role

**AI/ML feature (P1):**
```
1. Define or update contract in shared/contracts/
2. Write parser/chunker logic in services/ai/
3. Log steps to Langfuse
4. Connect to embedder/Qdrant
```

**Backend feature (P2):**
```
1. DB migration in services/api/db/migrations/
2. SQLAlchemy model in services/api/db/models/
3. API endpoint in services/api/
4. Test with curl or /docs
```

**Frontend feature (P3):**
```
1. Component structure in apps/web/app/
2. Static UI first
3. Connect to API
4. Handle loading & error states
```

**Infra feature (P4):**
```
1. Update docker-compose.yml or infra/
2. Test locally with docker compose up -d
3. Update .env.example if new vars added
4. Verify all services healthy with docker compose ps
```

---

## Commit Message Rules

| Prefix | When to use |
|---|---|
| `feat:` | New feature or functionality |
| `fix:` | Bug fix |
| `chore:` | Config, tooling, dependencies |
| `docs:` | Documentation only |
| `refactor:` | Code restructure, no behavior change |
| `test:` | Adding or fixing tests |
| `changelog:` | CHANGELOG.md updates only |

Examples:
```bash
git commit -m "feat: add chunker.py with sliding window logic"
git commit -m "feat: add POST /persona endpoint"
git commit -m "fix: handle null persona name in response"
git commit -m "chore: add .dockerignore for web service"
git commit -m "changelog: Sprint 1 Day 3 complete"
```

---

## Sprint Feature Sizing

| Size | Time | Example |
|---|---|---|
| Small | 1–2 hours | Add env variable, fix a bug, update config |
| Medium | Half day | New API endpoint, new DB table, new UI component |
| Large | 1–2 days | Full flow — DB + API + UI, auth, integrations |

> If a feature takes longer than 2 days → **split it into smaller PRs**

---

## PR Review Rules

- Every PR to `changelog` needs **P4 approval**
- Every PR from `changelog` to `main` needs **1 approval**
- Keep PRs small — max ~10 files changed ideally
- Reviewer checks: does it work? is it in the right folder? does it break anything?
- If blocked waiting for review, ping the reviewer directly

---

## Getting Started (New Team Member)

```powershell
# 1. Clone the repo
git clone https://github.com/persona-ai-project/persona-ai.git
cd persona-ai

# 2. Copy env file and fill in values (get from P4)
cp .env.example .env

# 3. Create ClickHouse config (PowerShell — Windows)
New-Item -Path "clickhouse-config.xml" -ItemType File -Force; Set-Content -Path "clickhouse-config.xml" -Value @'
<clickhouse>
    <remote_servers>
        <default>
            <shard>
                <replica>
                    <host>localhost</host>
                    <port>9000</port>
                    <user>clickhouse</user>
                    <password>clickhouse</password>
                </replica>
            </shard>
        </default>
    </remote_servers>
    <keeper_server>
        <tcp_port>9181</tcp_port>
        <server_id>1</server_id>
        <log_storage_path>/var/lib/clickhouse/coordination/log</log_storage_path>
        <snapshot_storage_path>/var/lib/clickhouse/coordination/snapshots</snapshot_storage_path>
        <coordination_settings>
            <operation_timeout_ms>10000</operation_timeout_ms>
            <session_timeout_ms>30000</session_timeout_ms>
            <raft_logs_level>warning</raft_logs_level>
        </coordination_settings>
        <raft_configuration>
            <server>
                <id>1</id>
                <hostname>localhost</hostname>
                <port>9444</port>
            </server>
        </raft_configuration>
    </keeper_server>
    <zookeeper>
        <node>
            <host>localhost</host>
            <port>9181</port>
        </node>
    </zookeeper>
    <macros>
        <shard>1</shard>
        <replica>replica1</replica>
    </macros>
</clickhouse>
'@

# 4. Start all services
docker compose up -d

# 5. Verify everything is running
docker compose ps
```

Open http://localhost:3001 → ask P4 to add you to the Langfuse org.
Open http://localhost:3002 → web app should be running.
Open http://localhost:8001/docs → API swagger UI.

---

## Service Credentials (Local Only)

| Service | URL | Username | Password |
|---|---|---|---|
| Langfuse | http://localhost:3001 | Google OAuth | ask P4 for org invite |
| Web app | http://localhost:3002 | — | — |
| API docs | http://localhost:8001/docs | — | — |
| MinIO | http://localhost:9001 | minio | minio123 |
| Postgres (app DB) | localhost:5432 | postgres | postgres — DB: app |
| Postgres (persona DB) | localhost:5432 | postgres | postgres — DB: persona |
| ClickHouse | localhost:8123 | clickhouse | clickhouse |

> Never use these credentials in production. Never commit real `.env` values.

---

## Quick Reference

```bash
# Start everything
docker compose up -d

# Stop everything (keep data)
docker compose down

# Full reset (wipe all data)
docker compose down -v

# View logs
docker compose logs langfuse -f
docker compose logs api -f
docker compose logs web -f

# Check all service status
docker compose ps

# Restart one service
docker compose restart api

# Rebuild one service after Dockerfile changes
docker compose build api --no-cache
docker compose up -d api

# Verify DB tables
docker exec -it postgres psql -U postgres -d persona -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"

# Run API migrations manually
cd services/api
python -m alembic upgrade head

# Start your day
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Save your work
git add .
git commit -m "feat: what you built"
git push origin feature/your-feature-name

# Open PR → changelog (on GitHub)
# Wait for P4 review and merge

# After merged to changelog → P4 opens PR changelog → main
# After merged to main, clean up:
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```
