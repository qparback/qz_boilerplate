#!/usr/bin/env bash
# Restore the dev dump into the test DB (port 5433).
# Run db_dump_dev.sh first.

set -euo pipefail

source env/.env.test.config
source env/.env.test 2>/dev/null || {
    echo "Error: env/.env.test not found — copy env/.env.example first"
    exit 1
}

DUMP_FILE="tests/fixtures/dev_dump.sql"

if [ ! -f "$DUMP_FILE" ]; then
    echo "Error: $DUMP_FILE missing — run scripts/db_dump_dev.sh first"
    exit 1
fi

echo "Restoring $DUMP_FILE into test DB..."
PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h localhost \
    -p 5433 \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -f "$DUMP_FILE"

echo "Done."
