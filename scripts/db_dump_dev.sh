#!/usr/bin/env bash
# Dump the dev database to tests/fixtures/dev_dump.sql for use in test seeding.
# Usage: bash scripts/db_dump_dev.sh   (or: make test-from-dev)

set -euo pipefail

source env/.env.dev.config
source env/.env.dev 2>/dev/null || {
    echo "Error: env/.env.dev not found — copy env/.env.example first"
    exit 1
}

DUMP_FILE="tests/fixtures/dev_dump.sql"

echo "Dumping dev database to $DUMP_FILE..."
docker exec "${PROJECT_NAME}-db" pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --no-owner \
    --no-privileges \
    > "$DUMP_FILE"

echo "Done. $(wc -l < "$DUMP_FILE") lines written."
