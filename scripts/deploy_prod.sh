#!/usr/bin/env bash
# Deploy to production. Same shape as deploy_test.sh but with PROD_SERVER.
# Usage: PROD_SERVER=user@host make deploy-prod
#
# This script is invoked by `make deploy-prod` AFTER an interactive confirm.

set -euo pipefail

: "${PROD_SERVER:?PROD_SERVER not set (e.g. user@prod.example.com)}"
REMOTE_PATH="${REMOTE_PATH:-/opt/myapp}"

echo "Deploying to PRODUCTION: $PROD_SERVER:$REMOTE_PATH"
echo "Pausing 3s — Ctrl-C to abort..."
sleep 3

rsync -avz --delete \
    --exclude='.env.dev' --exclude='.env.test' --exclude='.env.prod' \
    --exclude='__pycache__' --exclude='.git' --exclude='.venv' \
    --exclude='.pytest_cache' --exclude='*.dump' \
    --exclude='tests/fixtures/dev_dump.sql' \
    ./ "${PROD_SERVER}:${REMOTE_PATH}/"

scp env/.env.prod "${PROD_SERVER}:${REMOTE_PATH}/env/.env.prod"

ssh "$PROD_SERVER" bash -s -- "$REMOTE_PATH" <<'REMOTE_EOF'
set -euo pipefail
cd "$1"
ENV=prod make setup-server
ENV=prod make prod
ENV=prod make migrate
echo "Production deployment complete."
REMOTE_EOF
