# Persona AI — Makefile
# Usage: make <command>
# On Windows: install make via `winget install GnuWin32.Make`

.PHONY: up down restart logs migrate seed lint test build clean reset

## Start all services
up:
	docker compose up -d

## Stop all services (keeps data)
down:
	docker compose down

## Restart all services
restart:
	docker compose down && docker compose up -d

## View logs for all services
logs:
	docker compose logs -f

## View API logs only
logs-api:
	docker compose logs api -f

## View web logs only
logs-web:
	docker compose logs web -f

## Run database migrations
migrate:
	cd services/api && python -m alembic upgrade head

## Run seed script (creates demo user with 30 chunks)
seed:
	cd scripts && python seed_demo_user.py

## Check all service status
status:
	docker compose ps

## Rebuild API container
build-api:
	docker compose build api --no-cache
	docker compose up -d api

## Rebuild web container
build-web:
	docker compose build web --no-cache
	docker compose up -d web

## Run linter on Python files
lint:
	cd services/api && python -m flake8 . --max-line-length=100 --exclude=__pycache__,migrations

## Run tests
test:
	cd services/api && python -m pytest tests/ -v

## Full reset — wipes all data and restarts fresh
reset:
	docker compose down -v
	docker compose up -d
	sleep 10
	cd services/api && python -m alembic upgrade head

## Clean Python cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

## Show available commands
help:
	@echo "Available commands:"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View all logs"
	@echo "  make logs-api    - View API logs"
	@echo "  make logs-web    - View web logs"
	@echo "  make migrate     - Run DB migrations"
	@echo "  make seed        - Run demo seed script"
	@echo "  make status      - Check service status"
	@echo "  make build-api   - Rebuild API container"
	@echo "  make build-web   - Rebuild web container"
	@echo "  make lint        - Run Python linter"
	@echo "  make test        - Run tests"
	@echo "  make reset       - Full reset (wipes data)"
	@echo "  make clean       - Remove Python cache files"