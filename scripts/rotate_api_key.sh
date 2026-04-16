#!/usr/bin/env bash
# Rotate the API_KEY without downtime.
#
# Strategy: generate a new key, write it to env/.env.<env>, restart only
# the api container (Caddy and DB stay up), then print the new key for the
# operator to distribute to clients.
#
# Usage: ENV=prod bash scripts/rotate_api_key.sh

set -euo pipefail

ENV="${ENV:-dev}"
SECRETS_FILE="env/.env.${ENV}"

if [ ! -f "$SECRETS_FILE" ]; then
    echo "Error: $SECRETS_FILE not found"
    exit 1
fi

NEW_KEY="$(openssl rand -hex 32)"

# Replace existing API_KEY= line, or append if not present
if grep -q '^API_KEY=' "$SECRETS_FILE"; then
    if sed --version >/dev/null 2>&1; then
        sed -i "s|^API_KEY=.*|API_KEY=${NEW_KEY}|" "$SECRETS_FILE"
    else
        sed -i '' "s|^API_KEY=.*|API_KEY=${NEW_KEY}|" "$SECRETS_FILE"
    fi
else
    echo "API_KEY=${NEW_KEY}" >> "$SECRETS_FILE"
fi

echo "Wrote new API_KEY to $SECRETS_FILE"

source env/.env.${ENV}.config
echo "Restarting ${PROJECT_NAME}-api..."
docker restart "${PROJECT_NAME}-api"

echo
echo "New API_KEY: ${NEW_KEY}"
echo "Distribute to clients now. Old key is no longer accepted."
