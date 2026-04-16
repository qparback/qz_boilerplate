# Architecture

## Container topology

```
                     ┌─────────────────────────────┐
   :80 / :443 ──────►│  app-caddy   (Caddy)        │
                     └────────────┬────────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────────┐
                     │  app-api     (FastAPI)      │
                     │   ├─ /health     (public)   │
                     │   ├─ /api/v1/*   (key auth) │
                     │   └─ /admin/*    (IP auth)  │
                     └────────────┬────────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────────┐
                     │  app-db      (Postgres 16)  │
                     └─────────────────────────────┘
                                  ▲
                                  │
                     ┌─────────────────────────────┐
                     │  app-scheduler (APScheduler)│
                     └─────────────────────────────┘
```

All services share an external Docker network `${PROJECT_NAME}-net` and the
DB volume `${PROJECT_NAME}_pgdata` is also external, so `docker compose down`
never destroys data.

## Layered code architecture

```
HTTP request
    │
    ▼
api/main.py            ── app factory, router registration
    │
    ▼
api/middleware.py      ── request ID, logging
    │
    ▼
api/security.py        ── x-api-key check
    │
    ▼
api/routers/<x>.py     ── HTTP endpoints (thin)
    │
    ▼
api/services/<x>.py    ── business logic (extends CRUDBase)
    │
    ▼
api/models/<x>.py      ── ORM mapping
    │
    ▼
api/database.py        ── async SQLAlchemy session
    │
    ▼
PostgreSQL
```

## Why these specific choices

- **Async SQLAlchemy 2.0 + asyncpg**: matches FastAPI's async I/O model.
  psycopg (sync) is also installed for Alembic, which itself is sync.
- **uv** instead of pip: fast, deterministic, lockfile-based.
- **Caddy** instead of Nginx: automatic Let's Encrypt, simpler config.
- **APScheduler in its own container**: scaling and restart independent of API.
- **Prompts in DB**: tune AI behavior without redeploys; admin UI to edit.
- **External volume + network**: `docker compose down -v` is safe.
- **Init script + Alembic baseline**: bootstrap is fast (raw SQL); ongoing
  changes are versioned (Alembic).
- **Audit log writes never fail the user request**: data integrity > log integrity.
- **Optional external-service keys**: scheduler container boots without
  Anthropic/Postmark keys configured.

## Request flow (a typical protected endpoint)

1. Client sends `GET /api/v1/users/123` with header `x-api-key: <key>`
2. Caddy matches `handle_path /api/*`, strips `/api`, forwards `/v1/users/123`
   to `app-api:8000`
3. `RequestIDMiddleware` attaches `request.state.request_id`
4. `verify_api_key` dependency checks the header against `settings.api_key`
   (constant-time compare). Sets `request.state.actor_key`.
5. The route handler resolves `db: AsyncSession = Depends(get_db)`
6. Handler calls `user_service.get_or_404(db, 123)`
7. Service issues a SELECT, returns `User`
8. Handler returns Pydantic response model → JSON
9. Middleware logs `GET /v1/users/123 200 12ms [abc123]`
10. `get_db` commits the session

If anything raises:
- `RequestValidationError` → 422 with structured detail
- Anything else → 500 + ERROR row in `app_logs`
