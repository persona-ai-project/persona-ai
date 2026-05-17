# Persona AI — Team Workflow Guide

## Current Infrastructure (Day 1 Complete ✅)

All services run locally via Docker. After cloning and running `docker compose up -d`:

| Service | URL | Purpose |
|---|---|---|
| Langfuse | http://localhost:3001 | AI observability & tracing dashboard |
| Postgres | localhost:5432 | Primary database |
| Redis | localhost:6379 | Caching & queues |
| Qdrant | http://localhost:6333 | Vector database for embeddings |
| MinIO | http://localhost:9001 | S3-compatible file storage |
| ClickHouse | localhost:8123 | Analytics database (used by Langfuse) |

---

## Repository Folder Structure

```
persona-ai/
│
├── apps/                   ← P3 (Frontend) — Next.js or React app lives here
│   └── web/                  UI pages, components, styles, public assets
│
├── services/               ← P2 (Backend) — All backend API services
│   └── api/                  Express/FastAPI endpoints, controllers, middleware
│
├── shared/                 ← P2 (Backend) + P1 (Lead) — Shared across services
│   ├── contracts/            API types, Zod schemas, shared interfaces (P2 owns)
│   ├── utils/                Shared utility functions
│   └── prisma/               DB schema and migrations (P2 owns)
│
├── infra/                  ← P1 (Lead) — Infrastructure & deployment config
│   ├── docker/               Additional Docker configs if needed
│   └── ci/                   GitHub Actions workflow files
│
├── scripts/                ← P1 (Lead) — Automation and helper scripts
│   └── seed.ts               DB seed scripts, setup helpers
│
├── docs/                   ← Everyone — Documentation
│   ├── architecture.md       System design (P1 writes)
│   ├── api.md                API reference (P2 writes)
│   ├── ai.md                 AI/prompt docs (P4 writes)
│   └── frontend.md           UI component docs (P3 writes)
│
├── .github/                ← P1 (Lead) — GitHub Actions CI/CD
│   └── workflows/
│       └── ci.yml
│
├── clickhouse-config.xml   ← P1 (Lead) — Do not modify without discussion
├── docker-compose.yml      ← P1 (Lead) — Do not modify without discussion
├── .env.example            ← P1 (Lead) — Add new variable names here (no real values)
├── .env                    ← NEVER commit — each person fills their own copy
├── .gitignore              ← P1 (Lead)
├── CHANGELOG.md            ← Everyone updates this each sprint
├── WORKFLOW.md             ← This file
├── README.md               ← P1 (Lead)
└── LICENSE
```

### Who owns what

| Person | Folders | Responsibility |
|---|---|---|
| **P1 — Lead** | `infra/`, `scripts/`, `.github/`, root config files | Docker, CI/CD, infra, PR reviews, env vars |
| **P2 — Backend** | `services/`, `shared/contracts/`, `shared/prisma/` | API endpoints, DB schema, migrations, shared types |
| **P3 — Frontend** | `apps/` | UI pages, components, routing, API integration |
| **P4 — AI/Data** | `services/ai/` (inside services), `docs/ai.md` | Langfuse traces, prompts, vector search, embeddings |

> **Rule:** You can read anyone's folder but only modify your own. Cross-folder changes need a discussion first.

---

## Branch Structure

```
main                  → stable, always working, no direct pushes
└── changelog         → running record of what's shipped each sprint
└── feature/*         → new features
└── fix/*             → bug fixes
└── chore/*           → config, tooling, non-feature work
└── docs/*            → documentation only changes
```

### Rules
- **No direct pushes to `main`** — everything goes through a PR
- **`main` requires 1 approval** before merge
- Keep branches short-lived — open PR within 2 days of starting

---

## How `changelog` Branch Works

`changelog` is a living record of everything shipped. It is **not** a feature branch.

### When to update it
Every time a PR merges into `main`, one team member (usually P1) updates `CHANGELOG.md`:

```bash
git checkout changelog
git pull origin changelog
git merge main
```

Open `CHANGELOG.md` and add an entry at the top:

```markdown
## [Sprint 1] - 2026-05-16

### Added
- Docker Compose with Postgres, Redis, Qdrant, Langfuse, MinIO, ClickHouse
- ClickHouse single-node Keeper config
- Google OAuth for Langfuse
- GitHub Actions CI skeleton
- Branch protection on main
- Full folder structure with .gitkeep placeholders

### Fixed
- ClickHouse missing CLICKHOUSE_USER env var
- ZooKeeper config error with ReplicatedMergeTree
- Missing NEXTAUTH_URL and S3 bucket env vars
```

Then commit and push:

```bash
git add CHANGELOG.md
git commit -m "changelog: sprint 1 foundation complete"
git push origin changelog
```

Then open a PR `changelog` → `main` so it's part of the permanent record.

---

## Daily Git Workflow (Every Team Member)

### Morning — start your day
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### During the day — commit often
```bash
git add .
git commit -m "feat: describe what you built"
```

### End of day — push and open PR
```bash
git push origin feature/your-feature-name
# Then open a Pull Request on GitHub → main
```

---

## Feature Workflow — Step by Step

### Step 1 — Pick your feature
Each sprint, features are assigned. Each feature = one branch = one PR.

### Step 2 — Create your branch from main
```bash
git checkout main
git pull origin main
git checkout -b feature/feature-name
```

Branch naming:
```
feature/user-auth
feature/chat-endpoint
feature/persona-creation-ui
feature/vector-search
fix/langfuse-connection
chore/update-env-example
docs/api-reference
```

### Step 3 — Add your files to the right folder

| You are | Your files go in |
|---|---|
| P1 — Lead | `infra/`, `scripts/`, `.github/workflows/` |
| P2 — Backend | `services/api/`, `shared/contracts/`, `shared/prisma/` |
| P3 — Frontend | `apps/web/` |
| P4 — AI/Data | `services/ai/`, `docs/ai.md` |

### Step 4 — Build in the right order

**Backend feature:**
```
1. DB migration (shared/prisma/)
2. Shared types/contracts (shared/contracts/)
3. API endpoint (services/api/)
4. Tests
```

**Frontend feature:**
```
1. Component structure (apps/web/components/)
2. Static UI
3. Connect to API
4. Handle loading & error states
```

**AI feature:**
```
1. Prompt definition
2. LangChain / AI service logic (services/ai/)
3. Log to Langfuse
4. Connect to API endpoint
```

### Step 5 — Commit with clear messages

| Prefix | When to use |
|---|---|
| `feat:` | New feature or functionality |
| `fix:` | Bug fix |
| `chore:` | Config, tooling, dependencies |
| `docs:` | Documentation only |
| `refactor:` | Code restructure, no behavior change |
| `test:` | Adding or fixing tests |

Examples:
```bash
git commit -m "feat: add user table migration"
git commit -m "feat: add POST /api/persona endpoint"
git commit -m "fix: handle null persona name"
git commit -m "docs: add API reference for persona endpoints"
```

### Step 6 — Open a Pull Request
- GitHub → Pull Requests → New PR
- Base: `main` ← Compare: `feature/your-branch`
- Write a clear title and 2-3 line description of what changed
- Request 1 reviewer
- Wait for approval before merging

### Step 7 — After merge, clean up
```bash
git checkout main
git pull origin main
git branch -d feature/your-feature-name
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

- Every PR needs **1 approval** before merge
- Keep PRs small — max ~10 files changed ideally
- Reviewer checks: does it work? is it in the right folder? does it break anything?
- If you're blocked waiting for review, ping the reviewer directly

---

## Getting Started (New Team Member)

```bash
# 1. Clone the repo
git clone https://github.com/persona-ai-project/persona-ai.git
cd persona-ai

# 2. Copy env file and fill in values (get values from P1)
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

Then open http://localhost:3001 and ask P1 to add you to the Langfuse org.

---

## Service Credentials (Local Only)

| Service | URL | Username | Password |
|---|---|---|---|
| Langfuse | http://localhost:3001 | Google OAuth | ask P1 for org invite |
| MinIO | http://localhost:9001 | minio | minio123 |
| Postgres | localhost:5432 | postgres | postgres |
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
docker compose logs postgres -f

# Check all service status
docker compose ps

# Restart one service
docker compose restart langfuse

# Start your day
git checkout main && git pull origin main
git checkout -b feature/your-feature-name

# Save and push your work
git add .
git commit -m "feat: what you built"
git push origin feature/your-feature-name

# Clean up after merge
git checkout main && git pull origin main
git branch -d feature/your-feature-name
```
