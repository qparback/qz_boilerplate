# FastAPI Boilerplate — Complete Build Instructions for Claude Code

## Purpose

This document instructs Claude Code to build a production-ready, reusable FastAPI boilerplate.
This is NOT a product — it is a foundation template that can be cloned for any new project.

## Core Principles

1. **Docker must work perfectly** — no guessing, no debugging, every command documented
2. **All AI prompts in database** — never hardcoded, always editable without redeploy
3. **Structured error handling** — important runs and errors logged to database
4. **Admin web interface** — service status, DB health, logs, roadmap
5. **Test framework** — unit tests + integration tests against real database
6. **Strict directory structure** — no files in wrong places, ever
7. **Security first** — Caddy, API keys, audit log
8. **All code commented in English**
9. **Deploy via scripts** — no CI/CD pipeline, simple and reliable

---

## Directory Structure

This structure is MANDATORY. Claude Code must never deviate from it.
Documentation files (.md) belong in /docs only. Never in project root except CLAUDE.md and README.md.

```
project-root/
│
├── CLAUDE.md                          # Claude Code instructions (this file)
├── README.md                          # Human-readable project overview
├── Makefile                           # All common commands
│
├── docker/                            # ALL Docker configuration — nothing Docker outside this dir
│   ├── docker-compose.yml             # Base compose (shared services)
│   ├── docker-compose.dev.yml         # Dev overrides (hot reload, exposed ports)
│   ├── docker-compose.test.yml        # Test environment
│   ├── docker-compose.prod.yml        # Production overrides
│   ├── caddy/
│   │   ├── Caddyfile.dev
│   │   └── Caddyfile.prod
│   ├── postgres/
│   │   └── init/
│   │       └── 01_schema.sql          # Initial schema, runs on first container start
│   └── dockerfiles/
│       ├── Dockerfile.api
│       ├── Dockerfile.scheduler
│       └── Dockerfile.admin
│
├── env/                               # Environment files — NEVER commit secrets
│   ├── .env.dev.config                # Non-secret dev config (committed)
│   ├── .env.test.config               # Non-secret test config (committed)
│   ├── .env.prod.config               # Non-secret prod config (committed)
│   ├── .env.dev                       # Dev secrets (gitignored)
│   ├── .env.test                      # Test secrets (gitignored)
│   ├── .env.prod                      # Prod secrets (gitignored)
│   ├── .env.example                   # Template — all keys, no values (committed)
│   └── .env.secrets.example           # Secret keys template (committed)
│
├── scripts/                           # Operational scripts
│   ├── deploy_test.sh                 # Deploy to test server
│   ├── deploy_prod.sh                 # Deploy to production server
│   ├── db_dump_dev.sh                 # Dump dev DB for test seeding
│   ├── db_restore_test.sh             # Restore dump into test DB
│   ├── create_network.sh              # One-time server setup
│   └── rotate_api_key.sh              # Rotate API key without downtime
│
├── api/                               # FastAPI application
│   ├── Dockerfile -> ../docker/dockerfiles/Dockerfile.api
│   ├── __init__.py
│   ├── main.py                        # App factory, router registration
│   ├── config.py                      # pydantic-settings Settings class
│   ├── security.py                    # API key verification dependency
│   ├── database.py                    # Async SQLAlchemy engine + session
│   ├── middleware.py                  # Request ID, logging, CORS
│   ├── exceptions.py                  # Global exception handlers
│   │
│   ├── models/                        # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py                    # BaseModel with id, created_at, updated_at
│   │   └── [resource].py              # One file per resource
│   │
│   ├── schemas/                       # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── base.py                    # Shared schema utilities
│   │   ├── pagination.py              # PaginatedResponse, PageParams
│   │   └── [resource].py              # Create, Update, Response per resource
│   │
│   ├── routers/                       # FastAPI routers
│   │   ├── __init__.py
│   │   └── [resource].py             # One router per resource
│   │
│   ├── services/                      # Business logic layer
│   │   ├── __init__.py
│   │   ├── crud_base.py               # Generic CRUD base class
│   │   └── [resource].py             # Resource-specific service
│   │
│   └── utils/                         # Shared utilities
│       ├── __init__.py
│       ├── claude_client.py           # Claude API wrapper
│       ├── memory_service.py          # Claude memory management
│       ├── email_service.py           # Postmark wrapper
│       ├── prompt_service.py          # Load prompts from database
│       └── audit_log.py               # Audit logging helper
│
├── scheduler/                         # APScheduler service
│   ├── Dockerfile -> ../docker/dockerfiles/Dockerfile.scheduler
│   ├── __init__.py
│   └── main.py                        # Scheduler setup + job registration
│
├── admin/                             # Admin web interface (served by FastAPI)
│   ├── __init__.py
│   ├── router.py                      # Admin routes
│   ├── templates/                     # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── logs.html
│   │   ├── prompts.html
│   │   └── roadmap.html
│   └── static/
│       └── admin.css
│
├── migrations/                        # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── tests/                             # All tests
│   ├── conftest.py                    # Shared fixtures, DB setup/teardown
│   ├── fixtures/                      # Test data
│   │   └── base_data.sql              # Known state for integration tests
│   ├── unit/                          # Unit tests (no DB)
│   │   └── test_[module].py
│   └── integration/                   # Integration tests (real DB)
│       └── test_[resource]_api.py
│
└── docs/                              # All documentation
    ├── architecture.md
    ├── api_reference.md
    ├── deployment.md
    └── roadmap.md                     # Also shown in admin UI
```

---

## Step 1 — Docker Configuration

### IMPORTANT: Docker lessons learned

These rules prevent the hours of Docker debugging that commonly occur:

1. **Always use `external: true`** for the main data volume and network — created once on server, never recreated by compose
2. **Never use `build: .`** — always specify explicit dockerfile path
3. **Always specify `restart: unless-stopped`** on all services except DB init containers
4. **Health checks on every service** — compose waits for healthy before starting dependents
5. **Never mount source code in production** — dev override only
6. **Use explicit image tags** — never `latest` in production
7. **Log rotation configured** — prevents disk fill
8. **ENV_FILE variable** — single variable controls which env files to load

### `docker/docker-compose.yml` (base — shared by all environments)

```yaml
# Base Docker Compose configuration
# Do NOT run this directly — use environment-specific overrides
# Usage: docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up

services:

  # ─── PostgreSQL Database ────────────────────────────────────────────────────
  app-db:
    container_name: ${PROJECT_NAME}-db
    image: postgres:16-alpine
    env_file:
      - ../env/${ENV_FILE}.config
      - ../env/${ENV_FILE}
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    networks:
      - app-net
    volumes:
      - app_pgdata:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    restart: unless-stopped

  # ─── FastAPI Application ────────────────────────────────────────────────────
  app-api:
    container_name: ${PROJECT_NAME}-api
    build:
      context: ..
      dockerfile: docker/dockerfiles/Dockerfile.api
    depends_on:
      app-db:
        condition: service_healthy
    env_file:
      - ../env/${ENV_FILE}.config
      - ../env/${ENV_FILE}
    environment:
      POSTGRES_HOST: ${PROJECT_NAME}-db
    networks:
      - app-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
    restart: unless-stopped

  # ─── Scheduler Service ──────────────────────────────────────────────────────
  app-scheduler:
    container_name: ${PROJECT_NAME}-scheduler
    build:
      context: ..
      dockerfile: docker/dockerfiles/Dockerfile.scheduler
    depends_on:
      app-db:
        condition: service_healthy
    env_file:
      - ../env/${ENV_FILE}.config
      - ../env/${ENV_FILE}
    environment:
      POSTGRES_HOST: ${PROJECT_NAME}-db
    networks:
      - app-net
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    restart: unless-stopped

  # ─── Caddy Reverse Proxy ────────────────────────────────────────────────────
  app-caddy:
    container_name: ${PROJECT_NAME}-caddy
    image: caddy:2-alpine
    depends_on:
      app-api:
        condition: service_healthy
    networks:
      - app-net
    volumes:
      - caddy_data:/data
      - caddy_config:/config
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    restart: unless-stopped

volumes:
  app_pgdata:
    external: true           # Created once: docker volume create ${PROJECT_NAME}_pgdata
  caddy_data:
  caddy_config:

networks:
  app-net:
    external: true           # Created once: docker network create ${PROJECT_NAME}-net
```

### `docker/docker-compose.dev.yml` (dev overrides)

```yaml
# Development overrides
# Usage: make dev

services:
  app-api:
    build:
      context: ..
      dockerfile: docker/dockerfiles/Dockerfile.api
      target: development
    volumes:
      - ../api:/app/api:ro          # Hot reload — mount source code
      - ../admin:/app/admin:ro
      - ../migrations:/app/migrations:ro
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"                 # Expose directly in dev for debugging

  app-db:
    ports:
      - "5432:5432"                 # Expose DB port in dev for DB tools

  app-caddy:
    volumes:
      - ./caddy/Caddyfile.dev:/etc/caddy/Caddyfile:ro
    ports:
      - "80:80"
```

### `docker/docker-compose.test.yml` (test environment)

```yaml
# Test environment — spun up by 'make test', torn down after
# Uses separate DB on port 5433 to avoid conflicts with dev

services:
  test-db:
    container_name: ${PROJECT_NAME}-test-db
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}_test
    ports:
      - "5433:5432"
    networks:
      - app-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 3s
      retries: 10
    tmpfs:
      - /var/lib/postgresql/data    # In-memory — fast, discarded after tests
```

### `docker/docker-compose.prod.yml` (production overrides)

```yaml
# Production overrides
# Usage: make prod (on server)

services:
  app-api:
    image: ${REGISTRY}/${PROJECT_NAME}-api:${VERSION}   # Use built image, not build
    deploy:
      resources:
        limits:
          memory: 512M

  app-scheduler:
    image: ${REGISTRY}/${PROJECT_NAME}-scheduler:${VERSION}

  app-caddy:
    volumes:
      - ./caddy/Caddyfile.prod:/etc/caddy/Caddyfile:ro
    ports:
      - "80:80"
      - "443:443"
```

### `docker/caddy/Caddyfile.dev`

```caddyfile
# Development Caddy — no TLS, simple proxy
:80 {
    # API routes
    handle /api/* {
        reverse_proxy app-api:8000
    }

    # Admin interface
    handle /admin/* {
        reverse_proxy app-api:8000
    }

    # Health check
    handle /health {
        reverse_proxy app-api:8000
    }
}
```

### `docker/caddy/Caddyfile.prod`

```caddyfile
# Production Caddy — automatic TLS via Let's Encrypt
{
    email {$ADMIN_EMAIL}
}

{$DOMAIN} {
    # Rate limiting — prevent abuse
    rate_limit {
        zone api {
            match {
                path /api/*
            }
            key {remote_host}
            events 100
            window 1m
        }
    }

    # API routes — protected by API key in FastAPI
    handle /api/* {
        reverse_proxy app-api:8000
    }

    # Admin interface — additional IP restriction
    handle /admin/* {
        @blocked not remote_ip {$ADMIN_IP_WHITELIST}
        abort @blocked
        reverse_proxy app-api:8000
    }

    handle /health {
        reverse_proxy app-api:8000
    }

    # Block common attack paths
    handle /.env* { abort }
    handle /.git* { abort }
}
```

### `docker/dockerfiles/Dockerfile.api`

```dockerfile
# ─── Base stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Development stage ────────────────────────────────────────────────────────
FROM base AS development
# Source code is mounted as volume in dev — no COPY needed
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ─── Production stage ─────────────────────────────────────────────────────────
FROM base AS production

# Copy application code
COPY api/ ./api/
COPY admin/ ./admin/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### `docker/dockerfiles/Dockerfile.scheduler`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scheduler/ ./scheduler/
COPY api/config.py ./api/config.py
COPY api/database.py ./api/database.py

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "scheduler.main"]
```

---

## Step 2 — Makefile

The Makefile is the single entry point for all operations.
Every developer command goes through `make`.

```makefile
# ─── Configuration ────────────────────────────────────────────────────────────
PROJECT_NAME ?= myapp
ENV ?= dev
ENV_FILE = env/.env.$(ENV)
COMPOSE_BASE = docker/docker-compose.yml
COMPOSE_ENV = docker/docker-compose.$(ENV).yml
COMPOSE = docker compose -f $(COMPOSE_BASE) -f $(COMPOSE_ENV) \
          --env-file $(ENV_FILE).config --env-file $(ENV_FILE)

.PHONY: help dev test prod stop logs ps shell db-shell migrate \
        test-run test-from-dev setup-server

# ─── Help ─────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  $(PROJECT_NAME) — Available commands"
	@echo ""
	@echo "  Development:"
	@echo "    make dev          Start development environment"
	@echo "    make stop         Stop all containers"
	@echo "    make logs         Follow all logs"
	@echo "    make ps           Show container status"
	@echo "    make shell        Open shell in API container"
	@echo "    make db-shell     Open psql in DB container"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate      Run Alembic migrations"
	@echo "    make migration m='message'  Create new migration"
	@echo ""
	@echo "  Testing:"
	@echo "    make test         Run full test suite (unit + integration)"
	@echo "    make test-unit    Run unit tests only"
	@echo "    make test-from-dev  Seed test DB from dev dump, then test"
	@echo ""
	@echo "  Deployment:"
	@echo "    make deploy-test  Deploy to test server"
	@echo "    make deploy-prod  Deploy to production server"
	@echo ""
	@echo "  Setup:"
	@echo "    make setup-server  One-time server setup (network + volumes)"
	@echo ""

# ─── Development ──────────────────────────────────────────────────────────────
dev:
	@echo "Starting development environment..."
	ENV=dev $(COMPOSE) up --build -d
	@echo "✅ Running at http://localhost"
	@echo "   API docs: http://localhost/api/docs"
	@echo "   Admin:    http://localhost/admin"

stop:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

shell:
	docker exec -it $(PROJECT_NAME)-api /bin/bash

db-shell:
	docker exec -it $(PROJECT_NAME)-db psql -U $$POSTGRES_USER -d $$POSTGRES_DB

# ─── Database ─────────────────────────────────────────────────────────────────
migrate:
	docker exec $(PROJECT_NAME)-api alembic upgrade head

migration:
	docker exec $(PROJECT_NAME)-api alembic revision --autogenerate -m "$(m)"

# ─── Testing ──────────────────────────────────────────────────────────────────
test:
	@echo "Starting test database..."
	ENV=test docker compose -f $(COMPOSE_BASE) -f docker/docker-compose.test.yml \
	  --env-file env/.env.test.config --env-file env/.env.test \
	  up test-db -d
	@echo "Waiting for test DB to be healthy..."
	@sleep 5
	@echo "Running migrations on test DB..."
	DATABASE_URL=postgresql+asyncpg://$$POSTGRES_USER:$$POSTGRES_PASSWORD@localhost:5433/$$POSTGRES_DB_test \
	  alembic upgrade head
	@echo "Loading test fixtures..."
	psql postgresql://$$POSTGRES_USER:$$POSTGRES_PASSWORD@localhost:5433/$$POSTGRES_DB_test \
	  -f tests/fixtures/base_data.sql
	@echo "Running tests..."
	pytest tests/ -v --tb=short
	@echo "Tearing down test database..."
	ENV=test docker compose -f $(COMPOSE_BASE) -f docker/docker-compose.test.yml \
	  --env-file env/.env.test.config --env-file env/.env.test \
	  down

test-unit:
	pytest tests/unit/ -v --tb=short

test-from-dev:
	@echo "Dumping dev database..."
	bash scripts/db_dump_dev.sh
	@echo "Restoring into test database..."
	bash scripts/db_restore_test.sh
	@echo "Running tests against dev data..."
	pytest tests/ -v --tb=short -m "not requires_clean_data"

# ─── Deployment ───────────────────────────────────────────────────────────────
deploy-test:
	bash scripts/deploy_test.sh

deploy-prod:
	@echo "⚠️  Deploying to PRODUCTION. Are you sure? [y/N]"
	@read ans && [ $${ans:-N} = y ] && bash scripts/deploy_prod.sh

# ─── Setup ────────────────────────────────────────────────────────────────────
setup-server:
	@echo "Creating Docker network and volumes..."
	docker network create $(PROJECT_NAME)-net || true
	docker volume create $(PROJECT_NAME)_pgdata || true
	@echo "✅ Server setup complete"
```

---

## Step 3 — Environment Files

### `env/.env.example` (committed — all keys, no values)

```
# Application
PROJECT_NAME=myapp
APP_ENV=dev
DOMAIN=myapp.example.com
ADMIN_EMAIL=admin@example.com
ADMIN_IP_WHITELIST=127.0.0.1

# Database
POSTGRES_HOST=app-db
POSTGRES_PORT=5432
POSTGRES_DB=myapp
POSTGRES_USER=
DATABASE_URL=

# API Security
API_KEY=

# Anthropic Claude
ANTHROPIC_API_KEY=

# Postmark Email
POSTMARK_SERVER_TOKEN=
POSTMARK_FROM_EMAIL=
POSTMARK_FROM_NAME=

# Scheduler
SCHEDULER_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_TO_DB=true
```

### `env/.env.dev.config` (committed — non-secret dev config)

```
APP_ENV=dev
PROJECT_NAME=myapp
POSTGRES_HOST=myapp-db
POSTGRES_PORT=5432
POSTGRES_DB=myapp
LOG_LEVEL=DEBUG
LOG_TO_DB=true
SCHEDULER_ENABLED=true
```

---

## Step 4 — Database Schema

### `docker/postgres/init/01_schema.sql`

This runs automatically on first container start. All tables use UUID primary keys
and include created_at/updated_at. All text columns use TEXT not VARCHAR.

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── System tables ────────────────────────────────────────────────────────────

-- AI Prompts — all prompts stored here, never hardcoded
CREATE TABLE IF NOT EXISTS prompts (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key         TEXT UNIQUE NOT NULL,      -- e.g. 'weekly_brief_system'
    name        TEXT NOT NULL,             -- Human-readable name
    description TEXT,                      -- What this prompt does
    content     TEXT NOT NULL,             -- The actual prompt text
    model       TEXT DEFAULT 'claude-sonnet-4-6',
    temperature FLOAT DEFAULT 0.7,
    max_tokens  INTEGER DEFAULT 2000,
    active      BOOLEAN DEFAULT TRUE,
    version     INTEGER DEFAULT 1,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Application logs — important operations and errors
CREATE TABLE IF NOT EXISTS app_logs (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level        TEXT NOT NULL CHECK (level IN ('DEBUG','INFO','WARNING','ERROR','CRITICAL')),
    service      TEXT NOT NULL,            -- 'api', 'scheduler', 'admin'
    operation    TEXT NOT NULL,            -- What was being done
    message      TEXT NOT NULL,
    details      JSONB,                    -- Additional structured data
    request_id   TEXT,                     -- Correlates with HTTP request
    duration_ms  INTEGER,                  -- How long the operation took
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_app_logs_level ON app_logs(level);
CREATE INDEX idx_app_logs_service ON app_logs(service);
CREATE INDEX idx_app_logs_created_at ON app_logs(created_at DESC);

-- Audit log — who did what, when (mutations only)
CREATE TABLE IF NOT EXISTS audit_log (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation    TEXT NOT NULL,            -- 'CREATE', 'UPDATE', 'DELETE'
    resource     TEXT NOT NULL,            -- Table/resource name
    resource_id  TEXT,                     -- ID of affected record
    actor_key    TEXT,                     -- API key identifier (hashed)
    ip_address   TEXT,
    request_id   TEXT,
    old_values   JSONB,                    -- Previous state (UPDATE/DELETE)
    new_values   JSONB,                    -- New state (CREATE/UPDATE)
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_resource ON audit_log(resource, resource_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- Email log — all outbound emails
CREATE TABLE IF NOT EXISTS email_log (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_type          TEXT NOT NULL,
    recipient_email     TEXT NOT NULL,
    subject             TEXT,
    postmark_message_id TEXT,
    status              TEXT DEFAULT 'sent' CHECK (status IN ('sent','failed','bounced')),
    error_message       TEXT,
    metadata            JSONB,
    sent_at             TIMESTAMPTZ DEFAULT NOW()
);

-- Memory files — Claude AI memory per user/context
CREATE TABLE IF NOT EXISTS memory_files (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_key TEXT NOT NULL,             -- e.g. 'user_123_company_456'
    file_key    TEXT NOT NULL,             -- e.g. 'profile', 'history'
    content     TEXT NOT NULL,             -- Markdown content
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(context_key, file_key)
);

-- Roadmap — shown in admin UI
CREATE TABLE IF NOT EXISTS roadmap_items (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phase       TEXT NOT NULL,             -- 'MVP', 'Phase 2', etc.
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT DEFAULT 'planned' CHECK (status IN ('planned','in_progress','done','cancelled')),
    priority    INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default prompt examples
INSERT INTO prompts (key, name, description, content) VALUES
(
    'example_system',
    'Example System Prompt',
    'Example prompt — replace with your actual prompts',
    'You are a helpful assistant. Be concise and accurate.'
),
(
    'example_user_template',
    'Example User Prompt Template',
    'Template with {variable} placeholders replaced at runtime',
    'Please help with the following: {task}\n\nContext: {context}'
)
ON CONFLICT (key) DO NOTHING;
```

---

## Step 5 — FastAPI Application

### `api/config.py`

```python
"""
Application configuration.
All settings loaded from environment variables via pydantic-settings.
Never hardcode secrets — always use environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central configuration class.
    Environment variables are automatically mapped to these fields.
    """

    # Application
    app_env: str = "dev"
    project_name: str = "myapp"
    log_level: str = "INFO"
    log_to_db: bool = True

    # Database
    database_url: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str

    # Security
    api_key: str
    admin_ip_whitelist: str = "127.0.0.1"

    # Anthropic
    anthropic_api_key: str

    # Postmark
    postmark_server_token: str
    postmark_from_email: str
    postmark_from_name: str = "MyApp"

    # Scheduler
    scheduler_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",       # Ignore unknown env vars — prevents startup failures
        case_sensitive=False
    )

    @property
    def is_dev(self) -> bool:
        return self.app_env == "dev"

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once at startup."""
    return Settings()


# Module-level convenience import
settings = get_settings()
```

### `api/security.py`

```python
"""
API security — key-based authentication.
All protected routes use the verify_api_key dependency.
"""

import hashlib
from fastapi import HTTPException, Security, status, Request
from fastapi.security import APIKeyHeader
from api.config import settings

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def hash_key(key: str) -> str:
    """Hash API key for safe storage in audit log."""
    return hashlib.sha256(key.encode()).hexdigest()[:16]


async def verify_api_key(
    request: Request,
    api_key: str = Security(api_key_header)
) -> str:
    """
    FastAPI dependency — verifies x-api-key header.
    Raises 403 if key is missing or incorrect.
    Returns hashed key for audit logging.
    """
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key"
        )
    return hash_key(api_key)
```

### `api/middleware.py`

```python
"""
Request middleware.
Adds request ID to every request for log correlation.
Logs request/response in structured format.
"""

import uuid
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attaches a unique request ID to every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        request.state.start_time = time.time()

        response = await call_next(request)

        duration_ms = int((time.time() - request.state.start_time) * 1000)
        response.headers["X-Request-ID"] = request_id

        # Log all requests except health checks
        if request.url.path != "/health":
            logger.info(
                "%s %s %d %dms [%s]",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                request_id
            )

        return response
```

### `api/exceptions.py`

```python
"""
Global exception handlers.
All unhandled exceptions return structured JSON responses.
Errors are logged to database for critical operations.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the app."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors — return 422 with details."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "detail": exc.errors(),
                "request_id": getattr(request.state, "request_id", None)
            }
        )

    @app.exception_handler(Exception)
    async def general_error_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle all unhandled exceptions — return 500."""
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "Unhandled exception on %s %s [%s]: %s",
            request.method,
            request.url.path,
            request_id,
            str(exc),
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "request_id": request_id
            }
        )
```

### `api/database.py`

```python
"""
Database connection and session management.
Uses SQLAlchemy 2.0 async with asyncpg driver.
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from api.config import settings


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.is_dev,      # Log SQL in dev only
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True         # Verify connections before use
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields database session, auto-closes after request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### `api/models/base.py`

```python
"""
Base SQLAlchemy model.
All models inherit from this — provides id, created_at, updated_at.
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from api.database import Base


class BaseModel(Base):
    """
    Abstract base model.
    Provides UUID primary key and timestamp columns for all tables.
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
```

### `api/schemas/pagination.py`

```python
"""
Pagination schemas — used by all list endpoints.
"""

from typing import TypeVar, Generic, List
from pydantic import BaseModel

T = TypeVar("T")


class PageParams(BaseModel):
    """Query parameters for paginated endpoints."""
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response envelope."""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(cls, items: List[T], total: int, params: PageParams):
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=-(-total // params.page_size)  # Ceiling division
        )
```

### `api/services/crud_base.py`

```python
"""
Generic CRUD service base class.
All resource services inherit from this.
Add a new resource: create model, schema, router, and service that extends CRUDBase.
"""

from typing import TypeVar, Generic, Type, List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.base import BaseModel
from api.schemas.pagination import PageParams, PaginatedResponse

ModelType = TypeVar("ModelType", bound=BaseModel)


class CRUDBase(Generic[ModelType]):
    """
    Generic CRUD operations.
    Usage: class UserService(CRUDBase[User]):
               def __init__(self): super().__init__(User)
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        """Get single record by ID. Returns None if not found."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_or_404(self, db: AsyncSession, id: UUID) -> ModelType:
        """Get single record by ID. Raises 404 if not found."""
        from fastapi import HTTPException, status
        record = await self.get(db, id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} {id} not found"
            )
        return record

    async def list(
        self,
        db: AsyncSession,
        params: PageParams
    ) -> PaginatedResponse[ModelType]:
        """List records with pagination."""
        # Count total
        count_result = await db.execute(
            select(func.count()).select_from(self.model)
        )
        total = count_result.scalar()

        # Fetch page
        result = await db.execute(
            select(self.model)
            .order_by(self.model.created_at.desc())
            .offset(params.offset)
            .limit(params.page_size)
        )
        items = result.scalars().all()

        return PaginatedResponse.create(items=items, total=total, params=params)

    async def create(self, db: AsyncSession, data: dict) -> ModelType:
        """Create new record."""
        record = self.model(**data)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update(
        self,
        db: AsyncSession,
        id: UUID,
        data: dict
    ) -> ModelType:
        """Update existing record. Raises 404 if not found."""
        record = await self.get_or_404(db, id)
        for key, value in data.items():
            if value is not None:
                setattr(record, key, value)
        await db.flush()
        await db.refresh(record)
        return record

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        """Delete record. Returns True if deleted, False if not found."""
        record = await self.get(db, id)
        if not record:
            return False
        await db.delete(record)
        return True
```

### `api/main.py`

```python
"""
FastAPI application factory.
Registers all routers, middleware, and exception handlers.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.openapi.utils import get_openapi

from api.config import settings
from api.security import verify_api_key
from api.middleware import RequestIDMiddleware
from api.exceptions import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting %s in %s mode", settings.project_name, settings.app_env)
    yield
    logger.info("Shutting down %s", settings.project_name)


# ─── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=f"{settings.project_name} API",
    version="0.1.0",
    root_path="/api",
    servers=[{"url": "/api", "description": "Current environment"}],
    swagger_ui_parameters={"displayRequestDuration": True},
    lifespan=lifespan
)

# ─── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(RequestIDMiddleware)

# ─── Exception handlers ───────────────────────────────────────────────────────
register_exception_handlers(app)

# ─── Public routes ────────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
async def health():
    """Health check — always public, always returns 200 if app is running."""
    return {"status": "ok", "env": settings.app_env}

# ─── Protected routes ─────────────────────────────────────────────────────────
# Add new routers here as the project grows:
# from api.routers import users_router
# app.include_router(users_router, prefix="/v1", dependencies=[Depends(verify_api_key)])

# ─── Admin interface ──────────────────────────────────────────────────────────
from admin.router import router as admin_router
app.include_router(admin_router)    # Admin has its own IP-based auth via Caddy

# ─── OpenAPI customization ────────────────────────────────────────────────────
def custom_openapi():
    """Customize OpenAPI schema to include API key auth."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes
    )
    schema["servers"] = [{"url": "/api", "description": "Current environment"}]
    schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "x-api-key"
        }
    }
    schema["security"] = [{"APIKeyHeader": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi
```

---

## Step 6 — Utility Services

### `api/utils/prompt_service.py`

```python
"""
Prompt service — loads AI prompts from database.
Prompts are NEVER hardcoded. Always fetched from the prompts table.
Use prompt keys as constants to avoid typos.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class PromptNotFoundError(Exception):
    """Raised when a prompt key does not exist in database."""
    pass


async def get_prompt(db: AsyncSession, key: str) -> dict:
    """
    Load a prompt by key from the database.
    Returns dict with: content, model, temperature, max_tokens.
    Raises PromptNotFoundError if key not found.
    """
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT content, model, temperature, max_tokens FROM prompts WHERE key = :key AND active = TRUE"),
        {"key": key}
    )
    row = result.fetchone()
    if not row:
        raise PromptNotFoundError(f"Prompt '{key}' not found in database")
    return {
        "content": row.content,
        "model": row.model,
        "temperature": row.temperature,
        "max_tokens": row.max_tokens
    }


async def render_prompt(db: AsyncSession, key: str, variables: dict) -> dict:
    """
    Load prompt and render template variables.
    Example: render_prompt(db, 'welcome_email', {'name': 'Anna', 'company': 'Acme'})
    """
    prompt = await get_prompt(db, key)
    try:
        prompt["content"] = prompt["content"].format(**variables)
    except KeyError as e:
        logger.error("Missing variable %s in prompt '%s'", e, key)
        raise
    return prompt
```

### `api/utils/claude_client.py`

```python
"""
Claude API client wrapper.
All Anthropic API calls go through this class.
Handles retries, error logging, and memory integration.
"""

import logging
import time
from typing import Optional
import anthropic
from api.config import settings

logger = logging.getLogger(__name__)

# Initialize Anthropic client once at module level
_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


class ClaudeClient:
    """
    Wrapper around Anthropic SDK.
    Use this class for all Claude API calls — never call anthropic directly.
    """

    def __init__(self):
        self.client = _client

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        model: str = "claude-sonnet-4-6",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        context_key: Optional[str] = None
    ) -> str:
        """
        Send a completion request to Claude.

        Args:
            system_prompt: The system instructions
            user_message: The user message
            model: Claude model to use
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum response tokens
            context_key: If provided, memory files are loaded for this context

        Returns:
            The text response from Claude
        """
        start_time = time.time()

        messages = [{"role": "user", "content": user_message}]

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "Claude API call completed in %dms (model=%s, tokens_in=%d, tokens_out=%d)",
                duration_ms,
                model,
                response.usage.input_tokens,
                response.usage.output_tokens
            )
            return response.content[0].text

        except anthropic.APIError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Claude API error after %dms: %s",
                duration_ms,
                str(e)
            )
            raise

    async def complete_with_prompt(
        self,
        db,
        prompt_key: str,
        user_message: str,
        variables: dict = None
    ) -> str:
        """
        Complete using a prompt loaded from database.
        Combines prompt_service + claude_client in one call.
        """
        from api.utils.prompt_service import render_prompt
        prompt = await render_prompt(db, prompt_key, variables or {})
        return await self.complete(
            system_prompt=prompt["content"],
            user_message=user_message,
            model=prompt["model"],
            temperature=prompt["temperature"],
            max_tokens=prompt["max_tokens"]
        )


# Module-level singleton
claude = ClaudeClient()
```

### `api/utils/memory_service.py`

```python
"""
Claude memory management.
Stores and retrieves memory files per context (user, company, etc).
Memory is stored as markdown in the memory_files table.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def read_memory(
    db: AsyncSession,
    context_key: str,
    file_key: str
) -> str:
    """
    Read a memory file for a given context.
    Returns empty string if no memory exists yet.
    """
    result = await db.execute(
        text("""
            SELECT content FROM memory_files
            WHERE context_key = :context_key AND file_key = :file_key
        """),
        {"context_key": context_key, "file_key": file_key}
    )
    row = result.fetchone()
    return row.content if row else ""


async def write_memory(
    db: AsyncSession,
    context_key: str,
    file_key: str,
    content: str
) -> None:
    """
    Write or update a memory file.
    Uses upsert — creates if not exists, updates if exists.
    """
    await db.execute(
        text("""
            INSERT INTO memory_files (context_key, file_key, content, updated_at)
            VALUES (:context_key, :file_key, :content, NOW())
            ON CONFLICT (context_key, file_key)
            DO UPDATE SET content = EXCLUDED.content, updated_at = NOW()
        """),
        {"context_key": context_key, "file_key": file_key, "content": content}
    )
    logger.debug("Memory written: %s/%s", context_key, file_key)


async def get_full_context(
    db: AsyncSession,
    context_key: str
) -> str:
    """
    Get all memory files for a context, concatenated.
    Used to inject full context into Claude prompts.
    """
    result = await db.execute(
        text("""
            SELECT file_key, content FROM memory_files
            WHERE context_key = :context_key
            ORDER BY updated_at DESC
        """),
        {"context_key": context_key}
    )
    rows = result.fetchall()
    if not rows:
        return ""

    parts = []
    for row in rows:
        parts.append(f"## {row.file_key}\n{row.content}")
    return "\n\n".join(parts)
```

### `api/utils/email_service.py`

```python
"""
Email service — Postmark integration.
All outbound emails go through this class.
Every email is logged to the email_log table.
"""

import logging
from typing import Optional
from postmarker.core import PostmarkClient
from sqlalchemy.ext.asyncio import AsyncSession
from api.config import settings

logger = logging.getLogger(__name__)

# Initialize Postmark client once
_postmark = PostmarkClient(server_token=settings.postmark_server_token)


class EmailService:
    """
    Postmark email wrapper.
    Use send_email() for all outbound mail — never call Postmark directly.
    All emails are logged to database.
    """

    async def send_email(
        self,
        db: AsyncSession,
        to: str,
        subject: str,
        html_body: str,
        email_type: str,
        metadata: Optional[dict] = None,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send an email via Postmark and log to database.

        Args:
            db: Database session
            to: Recipient email address
            subject: Email subject
            html_body: HTML email body
            email_type: Category label for logging (e.g. 'weekly_brief')
            metadata: Optional dict for logging context
            text_body: Plain text fallback (auto-generated if not provided)

        Returns:
            True if sent successfully, False otherwise
        """
        postmark_id = None
        status = "failed"
        error_message = None

        try:
            response = _postmark.emails.send(
                From=f"{settings.postmark_from_name} <{settings.postmark_from_email}>",
                To=to,
                Subject=subject,
                HtmlBody=html_body,
                TextBody=text_body or "Please view this email in an HTML-capable client.",
                MessageStream="outbound"
            )
            postmark_id = response.get("MessageID")
            status = "sent"
            logger.info("Email sent to %s (type=%s, id=%s)", to, email_type, postmark_id)

        except Exception as e:
            error_message = str(e)
            logger.error("Email failed to %s (type=%s): %s", to, email_type, error_message)

        finally:
            # Always log the attempt
            await self._log_email(
                db=db,
                email_type=email_type,
                recipient=to,
                subject=subject,
                postmark_id=postmark_id,
                status=status,
                error_message=error_message,
                metadata=metadata
            )

        return status == "sent"

    async def _log_email(
        self,
        db: AsyncSession,
        email_type: str,
        recipient: str,
        subject: str,
        postmark_id: Optional[str],
        status: str,
        error_message: Optional[str],
        metadata: Optional[dict]
    ) -> None:
        """Log email to database — called automatically by send_email."""
        from sqlalchemy import text
        import json
        await db.execute(
            text("""
                INSERT INTO email_log
                (email_type, recipient_email, subject, postmark_message_id, status, error_message, metadata)
                VALUES (:type, :recipient, :subject, :postmark_id, :status, :error, :metadata)
            """),
            {
                "type": email_type,
                "recipient": recipient,
                "subject": subject,
                "postmark_id": postmark_id,
                "status": status,
                "error": error_message,
                "metadata": json.dumps(metadata) if metadata else None
            }
        )


# Module-level singleton
email_service = EmailService()
```

### `api/utils/audit_log.py`

```python
"""
Audit logging — records all data mutations.
Call log_mutation() in any route that creates, updates, or deletes data.
"""

import json
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


async def log_mutation(
    db: AsyncSession,
    operation: str,
    resource: str,
    resource_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None
) -> None:
    """
    Log a data mutation to the audit_log table.

    Args:
        db: Database session
        operation: 'CREATE', 'UPDATE', or 'DELETE'
        resource: Table or resource name (e.g. 'users', 'companies')
        resource_id: ID of the affected record
        actor_key: Hashed API key of the caller
        ip_address: Client IP address
        request_id: Request ID for correlation
        old_values: Previous state (for UPDATE/DELETE)
        new_values: New state (for CREATE/UPDATE)
    """
    try:
        await db.execute(
            text("""
                INSERT INTO audit_log
                (operation, resource, resource_id, actor_key, ip_address,
                 request_id, old_values, new_values)
                VALUES
                (:operation, :resource, :resource_id, :actor_key, :ip_address,
                 :request_id, :old_values, :new_values)
            """),
            {
                "operation": operation,
                "resource": resource,
                "resource_id": str(resource_id) if resource_id else None,
                "actor_key": actor_key,
                "ip_address": ip_address,
                "request_id": request_id,
                "old_values": json.dumps(old_values) if old_values else None,
                "new_values": json.dumps(new_values) if new_values else None
            }
        )
    except Exception as e:
        # Audit log failure should never break the main operation
        logger.error("Failed to write audit log: %s", str(e))
```

---

## Step 7 — Admin Interface

### `admin/router.py`

```python
"""
Admin web interface.
Accessible at /admin — protected by IP whitelist in Caddy (production).
Shows: service status, database health, logs, prompts, roadmap.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from api.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="admin/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Main admin dashboard — service status overview."""
    # Check DB health
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "error"

    # Recent errors
    result = await db.execute(
        text("""
            SELECT service, operation, message, created_at
            FROM app_logs WHERE level IN ('ERROR','CRITICAL')
            ORDER BY created_at DESC LIMIT 10
        """)
    )
    recent_errors = result.fetchall()

    # Email stats
    result = await db.execute(
        text("""
            SELECT status, COUNT(*) as count
            FROM email_log
            WHERE sent_at > NOW() - INTERVAL '24 hours'
            GROUP BY status
        """)
    )
    email_stats = {row.status: row.count for row in result.fetchall()}

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "db_status": db_status,
        "recent_errors": recent_errors,
        "email_stats": email_stats
    })


@router.get("/logs", response_class=HTMLResponse)
async def logs(
    request: Request,
    level: str = None,
    service: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Log viewer with filtering."""
    query = "SELECT * FROM app_logs WHERE 1=1"
    params = {}
    if level:
        query += " AND level = :level"
        params["level"] = level
    if service:
        query += " AND service = :service"
        params["service"] = service
    query += " ORDER BY created_at DESC LIMIT 100"

    result = await db.execute(text(query), params)
    logs = result.fetchall()

    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs,
        "filter_level": level,
        "filter_service": service
    })


@router.get("/prompts", response_class=HTMLResponse)
async def prompts(request: Request, db: AsyncSession = Depends(get_db)):
    """Prompt management — view and edit prompts."""
    result = await db.execute(
        text("SELECT * FROM prompts ORDER BY key")
    )
    prompts = result.fetchall()
    return templates.TemplateResponse("prompts.html", {
        "request": request,
        "prompts": prompts
    })


@router.get("/roadmap", response_class=HTMLResponse)
async def roadmap(request: Request, db: AsyncSession = Depends(get_db)):
    """Development roadmap."""
    result = await db.execute(
        text("SELECT * FROM roadmap_items ORDER BY phase, priority")
    )
    items = result.fetchall()
    return templates.TemplateResponse("roadmap.html", {
        "request": request,
        "items": items
    })
```

---

## Step 8 — Scheduler

### `scheduler/main.py`

```python
"""
APScheduler service.
Runs as a separate Docker container.
Add scheduled jobs here — they call API endpoints or services directly.
All job runs are logged to app_logs table.
"""

import logging
import os
import time
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


async def example_daily_job():
    """
    Example daily job.
    Replace with actual job logic.
    Always log start, success, and failures.
    """
    logger.info("example_daily_job: starting")
    try:
        # Job logic here
        logger.info("example_daily_job: completed successfully")
    except Exception as e:
        logger.error("example_daily_job: failed — %s", str(e), exc_info=True)


async def main():
    """Main scheduler entry point."""
    scheduler = AsyncIOScheduler(timezone="Europe/Stockholm")

    # Register jobs
    scheduler.add_job(
        example_daily_job,
        CronTrigger(hour=7, minute=0),
        id="example_daily",
        replace_existing=True
    )

    scheduler.start()
    logger.info(
        "Scheduler started with %d jobs",
        len(scheduler.get_jobs())
    )

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    if enabled:
        asyncio.run(main())
    else:
        logger.info("Scheduler disabled (SCHEDULER_ENABLED=false)")
        while True:
            time.sleep(3600)
```

---

## Step 9 — Test Framework

### `tests/conftest.py`

```python
"""
Shared test fixtures.
Database is spun up fresh for each test session.
Use 'make test' to run the full suite with a clean database.
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from api.main import app
from api.database import get_db, Base
from api.config import settings

# Test database URL — always points to test DB on port 5433
TEST_DATABASE_URL = settings.database_url.replace(
    "@app-db:", "@localhost:"
).replace(":5432/", ":5433/").replace(
    f"/{settings.postgres_db}",
    f"/{settings.postgres_db}_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for all tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Database engine connected to test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db(test_engine) -> AsyncSession:
    """
    Database session for each test.
    Wraps each test in a transaction that is rolled back after the test.
    This means tests don't pollute each other.
    """
    async with test_engine.connect() as connection:
        await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False
        )
        async with session_factory() as session:
            yield session
        await connection.rollback()


@pytest.fixture
async def client(db) -> AsyncClient:
    """
    HTTP test client.
    Overrides the database dependency to use test DB.
    Includes API key header automatically.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"x-api-key": settings.api_key}
    ) as client:
        yield client
    app.dependency_overrides.clear()
```

### `tests/fixtures/base_data.sql`

```sql
-- Base test fixtures — known state for integration tests
-- This file is loaded by 'make test' before tests run

-- Example prompt for testing
INSERT INTO prompts (key, name, content, model, temperature, max_tokens) VALUES
('test_prompt', 'Test Prompt', 'You are a test assistant.', 'claude-sonnet-4-6', 0.5, 100)
ON CONFLICT (key) DO NOTHING;
```

### `tests/unit/test_crud_base.py`

```python
"""Unit tests for generic CRUD base — no database required."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from api.schemas.pagination import PageParams


def test_page_params_offset():
    """Test that pagination offset is calculated correctly."""
    params = PageParams(page=1, page_size=20)
    assert params.offset == 0

    params = PageParams(page=2, page_size=20)
    assert params.offset == 20

    params = PageParams(page=3, page_size=10)
    assert params.offset == 20
```

### `tests/integration/test_health.py`

```python
"""Integration tests for health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient):
    """Health endpoint should return 200 without auth."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_protected_route_requires_api_key(client: AsyncClient):
    """Protected routes should return 403 without API key."""
    response = await client.get("/api/v1/example", headers={"x-api-key": "wrong"})
    assert response.status_code == 403
```

---

## Step 10 — Deploy Scripts

### `scripts/deploy_test.sh`

```bash
#!/bin/bash
# Deploy to test server
# Usage: make deploy-test
# Requires: TEST_SERVER env var set, SSH key configured

set -e   # Exit on any error

TEST_SERVER="${TEST_SERVER:?TEST_SERVER not set}"
REMOTE_PATH="/opt/myapp"
ENV_FILE="env/.env.test"

echo "Deploying to test server: $TEST_SERVER"

# Sync code (exclude secrets and local files)
rsync -avz --exclude='.env.*' --exclude='__pycache__' --exclude='.git' \
  . ${TEST_SERVER}:${REMOTE_PATH}/

# Copy secrets separately (never in rsync glob above)
scp ${ENV_FILE} ${TEST_SERVER}:${REMOTE_PATH}/${ENV_FILE}

# Run on remote
ssh ${TEST_SERVER} << 'EOF'
  cd /opt/myapp
  ENV=test make prod
  docker exec myapp-api alembic upgrade head
  echo "✅ Test deployment complete"
EOF
```

### `scripts/db_dump_dev.sh`

```bash
#!/bin/bash
# Dump dev database for use in test seeding
# Usage: make test-from-dev

set -e

DUMP_FILE="tests/fixtures/dev_dump.sql"
source env/.env.dev

echo "Dumping dev database to $DUMP_FILE..."
docker exec myapp-db pg_dump \
  -U $POSTGRES_USER \
  -d $POSTGRES_DB \
  --no-owner \
  --no-privileges \
  > $DUMP_FILE

echo "✅ Dev database dumped to $DUMP_FILE"
echo "   Size: $(wc -l < $DUMP_FILE) lines"
```

---

## Step 11 — requirements.txt

```
# ─── Core ─────────────────────────────────────────────────────────────────────
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12
jinja2==3.1.4               # Admin templates

# ─── Database ─────────────────────────────────────────────────────────────────
sqlalchemy==2.0.41
asyncpg==0.30.0
psycopg[binary]==3.2.10
alembic==1.14.0

# ─── Configuration ────────────────────────────────────────────────────────────
pydantic==2.11.0
pydantic-settings==2.7.0
python-dotenv==1.1.0

# ─── Scheduler ────────────────────────────────────────────────────────────────
APScheduler>=3.10,<4
pytz==2025.2

# ─── AI ───────────────────────────────────────────────────────────────────────
anthropic>=0.40.0

# ─── Email ────────────────────────────────────────────────────────────────────
postmarker==1.0

# ─── Documents ────────────────────────────────────────────────────────────────
PyMuPDF==1.26.4
python-docx==1.1.0

# ─── HTTP ─────────────────────────────────────────────────────────────────────
httpx==0.28.0

# ─── Auth ─────────────────────────────────────────────────────────────────────
PyJWT==2.10.0
passlib[bcrypt]==1.7.4

# ─── Testing ──────────────────────────────────────────────────────────────────
pytest>=8.0.0
pytest-asyncio>=0.24.0
```

---

## Final Verification Checklist

After all steps are complete, run these commands in order.
Do NOT proceed to building product features until every check passes.

```bash
# 1. Docker starts clean
make dev
# Expected: All 4 containers "running"

# 2. Health check works
curl http://localhost/health
# Expected: {"status":"ok","env":"dev"}

# 3. Auth is enforced
curl http://localhost/api/v1/
# Expected: 403

curl -H "x-api-key: dev-key-change-me" http://localhost/api/docs
# Expected: 200 Swagger UI

# 4. Database has correct tables
make db-shell
\dt
# Expected: audit_log, app_logs, email_log, memory_files, prompts, roadmap_items

# 5. Admin interface loads
curl http://localhost/admin/
# Expected: 200 HTML dashboard

# 6. Scheduler is running
docker logs myapp-scheduler | head -5
# Expected: "Scheduler started with 1 jobs"

# 7. Tests pass
make test
# Expected: All tests green

# 8. Prompt is in database
make db-shell
SELECT key, name FROM prompts;
# Expected: example_system, example_user_template, test_prompt
```

---

## Adding a New Resource (Pattern to Follow)

When the boilerplate is built and you add a real resource (e.g. "users"):

1. **Model** — `api/models/user.py` extends `BaseModel`
2. **Schema** — `api/schemas/user.py` with `UserCreate`, `UserUpdate`, `UserResponse`
3. **Service** — `api/services/user.py` extends `CRUDBase[User]`
4. **Router** — `api/routers/user.py` with CRUD endpoints, includes audit_log calls
5. **Migration** — `make migration m="add users table"`
6. **Tests** — `tests/integration/test_users_api.py`
7. **Register** — add router to `api/main.py` protected section

This is the only pattern. Do not deviate from it.

---

## What NOT to Do

- Never put `.md` files in project root (except CLAUDE.md and README.md)
- Never hardcode prompts in Python files — always use prompt_service
- Never call Anthropic directly — always use claude_client
- Never call Postmark directly — always use email_service
- Never skip audit logging on mutations
- Never use `image: latest` in production Docker
- Never commit `.env.dev`, `.env.test`, `.env.prod` files
- Never put Docker config outside the `/docker` directory
- Never add new routes without following the model/schema/service/router pattern
