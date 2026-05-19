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