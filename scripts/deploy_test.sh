#!/usr/bin/env bash
# Deploy to the test server.
# Usage: TEST_SERVER=user@host make deploy-test
#
# Requires:
#   - SSH key configured for $TEST_SERVER
#   - $REMOTE_PATH exists on the server
#   - env/.env.test filled in locally (it gets scp'd separately from the rsync)

set -euo pipefail

: "${TEST_SERVER:?TEST_SERVER not set (e.g. user@test.example.com)}"
REMOTE_PATH="${REMOTE_PATH:-/opt/myapp}"

echo "Deploying to: $TEST_SERVER:$REMOTE_PATH"

# Sync code, excluding secrets and local artefacts
rsync -avz --delete \
    --exclude='.env.dev' --exclude='.env.test' --exclude='.env.prod' \
    --exclude='__pycache__' --exclude='.git' --exclude='.venv' \
    --exclude='.pytest_cache' --exclude='*.dump' \
    --exclude='tests/fixtures/dev_dump.sql' \
    ./ "${TEST_SERVER}:${REMOTE_PATH}/"

# Copy the secrets file separately
scp env/.env.test "${TEST_SERVER}:${REMOTE_PATH}/env/.env.test"

# Bring up the stack on the remote
ssh "$TEST_SERVER" bash -s -- "$REMOTE_PATH" <<'REMOTE_EOF'
set -euo pipefail
cd "$1"
ENV=test make setup-server
ENV=test make prod
ENV=test make migrate
echo "Test deployment complete."
REMOTE_EOF
