#!/usr/bin/env bash
# One-time setup — creates the external Docker network and data volume.
# Safe to re-run (idempotent).
#
# Usage: bash scripts/create_network.sh
#        Reads PROJECT_NAME from env/.env.${ENV:-dev}.config

set -euo pipefail

ENV="${ENV:-dev}"
CONFIG_FILE="env/.env.${ENV}.config"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found. Are you in the project root?"
    exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG_FILE"

if [ -z "${PROJECT_NAME:-}" ]; then
    echo "Error: PROJECT_NAME is not set in $CONFIG_FILE"
    exit 1
fi

NETWORK="${PROJECT_NAME}-net"
VOLUME="${PROJECT_NAME}_pgdata"

echo "Creating network: $NETWORK"
docker network create "$NETWORK" 2>/dev/null && echo "  created" || echo "  already exists"

echo "Creating volume: $VOLUME"
docker volume create "$VOLUME" >/dev/null && echo "  created or already exists"

echo
echo "Setup complete. You can now run: make dev"
