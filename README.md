# myapp — FastAPI Production Boilerplate

A reusable, production-ready FastAPI foundation. Clone this repo for any new
QuantumZero project. Replace the `myapp` placeholder with your project name
(`scripts/rename_project.sh` does it for you).

See [CLAUDE.md](CLAUDE.md) for the full architectural spec and rules.

---

## Quick start

```bash
# 1. Rename project (optional — defaults to "myapp")
bash scripts/rename_project.sh mynewapp

# 2. Copy env templates and fill in secrets
cp env/.env.example env/.env.dev
# Edit env/.env.dev — at minimum set API_KEY, POSTGRES_USER, POSTGRES_PASSWORD,
# DATABASE_URL, ANTHROPIC_API_KEY, POSTMARK_SERVER_TOKEN, POSTMARK_FROM_EMAIL

# 3. One-time server setup (creates external network + volume)
make setup-server

# 4. Lock dependencies
uv lock

# 5. Start dev environment
make dev

# 6. Verify
curl http://localhost/health
open http://localhost/api/docs
open http://localhost/admin/
```

---

## What's included

- **FastAPI** application with API key auth, request-ID middleware, structured exception handlers
- **Async SQLAlchemy 2.0** + Postgres 16 + Alembic migrations
- **Generic CRUD base** so adding a resource is a 4-file pattern
- **AI prompts in database** — never hardcoded, editable via admin UI
- **Claude API client** with retry + structured logging
- **Memory service** — per-context markdown files for Claude
- **Postmark email** with audit logging of every send
- **Audit log** for all data mutations
- **App log** to database for important operations + errors
- **Admin UI** (Jinja templates) — dashboard, logs, prompts, roadmap
- **APScheduler** as a separate container
- **Caddy** reverse proxy with automatic HTTPS in production
- **Docker** compose stack with dev/test/prod overrides
- **Test framework** — pytest with unit + integration suites against real DB
- **Deploy scripts** — simple SSH + rsync, no CI/CD pipeline required

## Project layout

See [CLAUDE.md](CLAUDE.md#directory-structure) for the strict directory layout
and the rationale.

## Common commands

| Command                | Purpose                                 |
| ---------------------- | --------------------------------------- |
| `make dev`             | Start dev environment (hot reload)      |
| `make stop`            | Stop all containers                     |
| `make logs`            | Follow logs from all services           |
| `make ps`              | Show container status                   |
| `make shell`           | Bash inside the API container           |
| `make db-shell`        | psql inside the DB container            |
| `make migrate`         | Run Alembic migrations                  |
| `make migration m=...` | Create a new migration                  |
| `make test`            | Full suite (unit + integration, real DB)|
| `make test-unit`       | Unit tests only                         |
| `make deploy-test`     | Deploy to test server                   |
| `make deploy-prod`     | Deploy to production (with confirm)     |

## Adding a new resource

Follow the pattern in [CLAUDE.md — Adding a New Resource](CLAUDE.md#adding-a-new-resource-pattern-to-follow).

1. Model in `api/models/`
2. Schema in `api/schemas/`
3. Service in `api/services/` (extends `CRUDBase`)
4. Router in `api/routers/`
5. `make migration m="add X table"` then `make migrate`
6. Tests in `tests/integration/`
7. Register router in `api/main.py`

## License

Internal QuantumZero. Not for redistribution.
