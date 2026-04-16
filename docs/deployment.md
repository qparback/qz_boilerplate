# Deployment

This boilerplate uses **scripts**, not CI/CD pipelines. Every deploy is a
deliberate `make` invocation from a developer machine.

## Initial server setup

On a fresh server:

```bash
# 1. Clone the repo
git clone <repo-url> /opt/myapp
cd /opt/myapp

# 2. Install Docker if needed
curl -fsSL https://get.docker.com | sh

# 3. Copy in the env secrets (NEVER committed)
scp env/.env.prod local-machine:/opt/myapp/env/.env.prod

# 4. Create network + volume (one-time)
ENV=prod make setup-server

# 5. First start
ENV=prod make prod

# 6. Mark migration baseline (one-time, only on first start)
ENV=prod make stamp-baseline
```

After step 5, the schema is created by `docker/postgres/init/01_schema.sql`
which runs once when the empty volume is mounted. Step 6 tells Alembic the
DB is at the baseline revision so future `make migrate` runs apply only
NEW migrations.

## Subsequent deploys

From your dev machine:

```bash
TEST_SERVER=user@test.example.com make deploy-test
PROD_SERVER=user@prod.example.com make deploy-prod    # interactive confirm
```

The deploy scripts:
1. `rsync` code to the server (excluding secrets and local artefacts)
2. `scp` the env secrets file separately (deliberately not in the rsync)
3. SSH in and run `make prod` (rebuilds containers if needed)
4. Run `make migrate` to apply any new Alembic migrations

## Rolling back

There is no automated rollback. Standard procedure:

```bash
# On the server
cd /opt/myapp
git fetch origin
git checkout <previous-good-sha>
ENV=prod make prod
# If a migration was the cause:
docker exec myapp-api alembic downgrade -1
```

## Rotating the API key

```bash
ENV=prod bash scripts/rotate_api_key.sh
# Prints the new key. Distribute to clients before they break.
```

## Monitoring

- `make logs` — tail all containers
- Admin dashboard `/admin/` — DB health, recent errors, email stats
- `app_logs` table — structured WARNING+ events from every service

## Backups

Not included. Recommended setup on the server:

```bash
# Daily pg_dump → S3 (cron)
0 2 * * * docker exec myapp-db pg_dump -U $POSTGRES_USER $POSTGRES_DB \
    | gzip | aws s3 cp - s3://backups/myapp/$(date +\%F).sql.gz
```
