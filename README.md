# myapp — FastAPI Production Boilerplate

A reusable, production-ready FastAPI foundation. Clone this repo for any new
QuantumZero project. Replace the `myapp` placeholder with your project name
(`scripts/rename_project.sh` does it for you).

See [CLAUDE.md](CLAUDE.md) for the full architectural spec and rules.

---

## Starting a new project from this boilerplate

The two-command happy path:

```bash
git clone https://github.com/qparback/qz_boilerplate.git mynewapp
cd mynewapp && bash scripts/init_project.sh mynewapp
```

`init_project.sh` does six things and then stops so you can watch Docker boot:

1. Renames `myapp` → your name across every file
2. Generates `env/.env.dev` and `env/.env.test` with random `POSTGRES_PASSWORD`
   and `API_KEY` (other external-service keys left blank — fill in when needed)
3. Runs `uv lock` to produce `uv.lock`
4. Runs `make setup-server` (creates the external Docker network + volume)
5. **Replaces `.git` with a fresh repo** and makes the initial commit
6. Prints the next commands to run

After it finishes:

```bash
make dev                                # build + start the stack
make stamp-baseline                     # one-time: tell Alembic the DB is at baseline

# Smoke tests
curl http://localhost/health
curl -H "x-api-key: $(grep ^API_KEY env/.env.dev | cut -d= -f2)" \
     http://localhost/api/v1/hello

# Push to a remote when ready
gh repo create your-org/mynewapp --private --source=. --push
```

That's it. You're now running a FastAPI + Postgres + Caddy stack with admin
UI, scheduler, audit log, prompts-in-database, and a real test framework.

## Manual setup

If you'd rather see what `init_project.sh` does, the steps individually are:

```bash
bash scripts/rename_project.sh mynewapp                      # rename
cp env/.env.example env/.env.dev && $EDITOR env/.env.dev     # fill in dev secrets
cp env/.env.example env/.env.test && $EDITOR env/.env.test   # fill in test secrets
uv lock                                                      # produce uv.lock
make setup-server                                            # docker network + volume
make dev                                                     # build + start
make stamp-baseline                                          # one-time
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

MIT — see [LICENSE](LICENSE). Use it, fork it, ship something cool.
