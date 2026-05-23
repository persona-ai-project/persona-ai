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