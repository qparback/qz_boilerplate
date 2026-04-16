# Roadmap

The roadmap is also stored in the `roadmap_items` database table and
displayed at `/admin/roadmap`. Edit it there for live changes; this file
is the long-form narrative.

## Done

- Initial scaffolding from `CLAUDE.md` spec
- Docker stack with dev/test/prod overrides
- Caddy reverse proxy (dev: HTTP, prod: HTTPS via Let's Encrypt)
- FastAPI app skeleton with API-key auth, request-ID middleware, exception handlers
- Async SQLAlchemy 2.0 + Postgres 16 + Alembic
- Generic `CRUDBase[Model]` for fast resource creation
- Prompts-in-database with admin UI
- Claude API client wrapper (lazy, optional ANTHROPIC_API_KEY)
- Postmark email service with email_log
- Audit log helper
- Memory service for per-context Claude memory
- Admin UI (Jinja templates, no JS framework)
- APScheduler service in its own container
- Test framework (unit + integration with real DB)
- Deploy scripts (test + prod) with rsync + ssh
- API key rotation script

## Next steps when starting a real project on top of this

1. Run `bash scripts/rename_project.sh <yourname>` to rename from `myapp`
2. Fill in `env/.env.dev` (and `.test`, `.prod` when ready)
3. Replace the example prompts in `01_schema.sql` with real ones
4. Add your first real resource following the 4-file pattern in CLAUDE.md
5. Replace example_daily_job in scheduler/main.py with real jobs
6. Update this roadmap with project-specific items
