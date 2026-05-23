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