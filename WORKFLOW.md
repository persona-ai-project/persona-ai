# Persona AI — Team Workflow Guide

## Current State (Day 1 Complete ✅)

All infrastructure is running locally via Docker:

| Service | URL | Purpose |
|---|---|---|
| Langfuse | http://localhost:3001 | AI observability & tracing |
| Postgres | localhost:5432 | Primary database |
| Redis | localhost:6379 | Caching & queues |
| Qdrant | http://localhost:6333 | Vector database |
| MinIO | http://localhost:9001 | File storage |
| ClickHouse | localhost:8123 | Analytics (Langfuse) |

---

## Branch Structure

```
main                  → stable, production-ready code only
└── changelog         → tracks what's shipped (auto-updated)
└── feature/*         → new features
└── fix/*             → bug fixes
└── chore/*           → config, tooling, non-feature work
```

### Rules
- **No one pushes directly to `main`** — everything goes through a PR
- **`main` requires 1 review** before merge
- `changelog` is updated every time something ships to `main`

---

## How `changelog` Branch Works

The `changelog` branch exists to track what has been built and shipped.

### When to update it
Every time a PR is merged into `main`, one team member updates `CHANGELOG.md`:

```bash
git checkout changelog
git pull origin changelog
git merge main
```

Then open `CHANGELOG.md` and add an entry:

```markdown
## [Sprint 1] - 2026-05-16

### Added
- Docker Compose setup with Postgres, Redis, Qdrant, Langfuse, MinIO, ClickHouse
- ClickHouse single-node Keeper config
- Google OAuth for Langfuse
- GitHub Actions CI skeleton
- Branch protection on main

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

Then open a PR from `changelog` → `main` so it's part of the permanent record.

---

## Daily Git Workflow (Every Team Member)

### Morning — start your day
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### During the day — save your work often
```bash
git add .
git commit -m "feat: describe what you built"
```

### End of day — push your branch
```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub targeting `main`.

---

## Feature Structure — How to Build a Feature

### Step 1 — Plan it first
Before writing any code, define:
- What does this feature do?
- Which service does it touch? (API, DB, frontend, AI?)
- Does it need a new DB table, endpoint, or UI component?

### Step 2 — Create your branch
```bash
git checkout main
git pull origin main
git checkout -b feature/feature-name
```

Branch naming examples:
```
feature/user-auth
feature/chat-endpoint
feature/persona-creation-ui
feature/vector-search
fix/langfuse-connection
chore/update-env-example
```

### Step 3 — Build in this order
For any backend feature:
```
1. DB schema / migration first
2. API endpoint / service logic
3. Tests
4. Connect to frontend (if needed)
```

For any frontend feature:
```
1. Component structure
2. Static UI
3. Connect to API
4. Handle loading & error states
```

### Step 4 — Commit as you go
```bash
# Good commit messages
git commit -m "feat: add user table migration"
git commit -m "feat: add POST /api/persona endpoint"
git commit -m "fix: handle null persona name"
git commit -m "chore: add .env variable for persona limit"
```

Commit message format:
| Prefix | When to use |
|---|---|
| `feat:` | New feature or functionality |
| `fix:` | Bug fix |
| `chore:` | Config, tooling, dependencies |
| `docs:` | Documentation only |
| `refactor:` | Code restructure, no behavior change |
| `test:` | Adding or fixing tests |

### Step 5 — Open a Pull Request
- Go to GitHub → Pull Requests → New PR
- Base: `main` ← Compare: `feature/your-branch`
- Write a clear title and describe what changed
- Request review from 1 teammate
- Wait for approval before merging

### Step 6 — After merge
```bash
# Clean up your local branch
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

---

## Sprint Feature Planning — When to Build What

### How sprints work
Each sprint = 1 week. At the start of each sprint:
1. Pick features from the backlog
2. Assign each feature to one person
3. Each feature = one branch = one PR

### Feature sizing guide
| Size | Time | Example |
|---|---|---|
| Small | 1–2 hours | Add a new env variable, fix a bug, update a config |
| Medium | half day | New API endpoint, new DB table, new UI component |
| Large | 1–2 days | Full flow (DB + API + UI), authentication, integrations |

If a feature is taking longer than 2 days, **split it** into smaller PRs.

### Who works on what (suggested structure)
```
P1 (Lead)     → Architecture, infra, Docker, CI/CD, reviews PRs
P2 (Backend)  → API endpoints, DB schema, shared contracts
P3 (Frontend) → UI components, pages, API integration
P4 (AI/Data)  → Langfuse traces, vector search, embeddings, prompts
```

---

## PR Review Rules

- Every PR needs **1 approval** before merge
- Reviewer checks: does it work? is it readable? does it break anything?
- Keep PRs small — easier to review, faster to merge
- If a PR has more than 10 files changed, consider splitting it

---

## Getting Started (New Team Member)

```bash
# 1. Clone
git clone https://github.com/persona-ai-project/persona-ai.git
cd persona-ai

# 2. Copy env
cp .env.example .env
# Fill in values — get them from the team lead

# 3. Create ClickHouse config (PowerShell)
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

# 4. Start services
docker compose up -d

# 5. Verify
docker compose ps
```

Open http://localhost:3001 — sign in with Google and ask team lead for org access in Langfuse.

---

## Quick Reference

```bash
# Start everything
docker compose up -d

# Stop everything (keep data)
docker compose down

# Full reset (wipe data)
docker compose down -v

# View logs
docker compose logs langfuse -f
docker compose logs postgres -f

# Check status
docker compose ps

# Start your feature
git checkout main && git pull origin main
git checkout -b feature/name

# End of day
git add . && git commit -m "feat: what you did"
git push origin feature/name
```
