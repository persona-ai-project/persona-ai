# Persona AI

AI-powered persona platform. Clone → configure → run.

---

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git
- Python 3.11+ (for local Alembic migrations)

### 1. Clone the repo
```bash
git clone https://github.com/persona-ai-project/persona-ai.git
cd persona-ai
```

### 2. Copy environment file
```bash
cp .env.example .env
```
Fill in the values — get credentials from P4.

### 3. Create ClickHouse config
Run this in PowerShell from the project root:
```powershell
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
```

### 4. Start all services
```bash
docker compose up -d
```

### 5. Run database migrations
```bash
cd services/api
python -m alembic upgrade head
cd ../..
```

### 6. Verify everything is running
```bash
docker compose ps
```

All services should show `Up` or `healthy`.

### 7. Verify API
Open http://localhost:8001/healthz → should return `{"status":"ok"}`

---

## Services

| Service | URL | Purpose |
|---|---|---|
| API (FastAPI) | http://localhost:8001 | Backend API + swagger at /docs |
| Web (Next.js) | http://localhost:3002 | Frontend app |
| Langfuse | http://localhost:3001 | AI observability dashboard |
| MinIO | http://localhost:9001 | File storage console |
| Qdrant | http://localhost:6333/dashboard | Vector DB dashboard |
| Postgres | localhost:5432 | Primary database |
| Redis | localhost:6379 | Cache and queues |
| ClickHouse | localhost:8123 | Analytics DB |

### Service credentials (local only)
| Service | User | Password | DB |
|---|---|---|---|
| Postgres | postgres | postgres | persona (our app), app (Langfuse) |
| ClickHouse | clickhouse | clickhouse | — |
| MinIO | minio | minio123 | — |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `R2_ENDPOINT` | Cloudflare R2 endpoint URL |
| `R2_ACCESS_KEY` | R2 API access key |
| `R2_SECRET_KEY` | R2 API secret key |
| `R2_AUDIO_BUCKET` | R2 bucket for audio files |
| `R2_INGEST_BUCKET` | R2 bucket for ingestion uploads |
| `NEXTAUTH_SECRET` | NextAuth secret (any random string) |
| `SALT` | Password salt (any random string) |

---

## Common Commands

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# View logs
docker compose logs api -f
docker compose logs web -f

# Run migrations
cd services/api && python -m alembic upgrade head

# Rebuild a service after code changes
docker compose build api --no-cache && docker compose up -d api

# Full reset (wipes all data)
docker compose down -v && docker compose up -d
```

---

## Troubleshooting

### Port already in use
```bash
# Find what is using the port (e.g. 8001)
netstat -ano | findstr :8001     # Windows
lsof -i :8001                    # Mac/Linux

# Then stop the conflicting process or change the port in docker-compose.yml
```

### Migration fails — "relation already exists"
The `persona` database already has tables from a previous run.
```bash
# Option 1: Check current migration state
cd services/api
python -m alembic current

# Option 2: Full reset (wipes persona DB data)
docker compose down -v
docker compose up -d
cd services/api && python -m alembic upgrade head
```

### Migration fails — "database does not exist"
```bash
docker exec -it postgres psql -U postgres -c "CREATE DATABASE persona;"
cd services/api && python -m alembic upgrade head
```

### API container keeps restarting
```bash
docker compose logs api --tail=30
# Look for the error and fix it, then:
docker compose build api --no-cache
docker compose up -d api
```

### ClickHouse fails — "No ZooKeeper configuration"
Make sure `clickhouse-config.xml` exists in the project root.
See Step 3 in Quick Start above.

### Web hot-reload not working
The web service uses webpack polling for hot-reload on Windows Docker.
Make sure `next.config.js` contains:
```js
webpack: (config) => {
  config.watchOptions = { poll: 1000, aggregateTimeout: 300 }
  return config
}
```

### Langfuse not loading
Check that ClickHouse and MinIO are healthy before Langfuse starts:
```bash
docker compose ps
# If clickhouse shows unhealthy, check its logs:
docker compose logs clickhouse --tail=20
```

### curl /healthz returns "connection refused"
The API container is not running. Check:
```bash
docker compose ps
docker compose logs api --tail=20
```

---

## Sprint 1 Deliverables ✅

- `docker compose up` → full stack live in under 90 seconds
- `alembic upgrade head` → 9 tables created in persona DB
- Every teammate can `curl http://localhost:8001/healthz`
- Chunk contract merged and frozen in `shared/contracts/chunk.py`
- R2 object storage configured with presigned URL support
- Ingestion job state machine sketched in `ingest/runner.py`