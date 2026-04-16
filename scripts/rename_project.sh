#!/usr/bin/env bash
# Rename the project from "myapp" to a new name across the repo.
# Usage: bash scripts/rename_project.sh mynewapp
#
# Run this once on a fresh clone before doing anything else.

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <new-project-name>"
    echo "  Example: $0 customer-portal"
    exit 1
fi

NEW_NAME="$1"
OLD_NAME="myapp"

if ! [[ "$NEW_NAME" =~ ^[a-z][a-z0-9_-]*$ ]]; then
    echo "Error: name must start with a lowercase letter and contain only [a-z0-9_-]"
    exit 1
fi

if [ "$NEW_NAME" = "$OLD_NAME" ]; then
    echo "Nothing to do — already named $OLD_NAME"
    exit 0
fi

echo "Renaming '$OLD_NAME' → '$NEW_NAME'..."

# File contents — limit to text files we control
FILES=$(grep -rl "$OLD_NAME" \
    --include="*.py" --include="*.yml" --include="*.yaml" \
    --include="*.toml" --include="*.md" --include="*.sh" \
    --include="*.html" --include="*.css" --include="*.ini" \
    --include="*.sql" --include="Caddyfile*" --include="Makefile" \
    --include=".env*" --include="Dockerfile*" \
    . 2>/dev/null || true)

if [ -n "$FILES" ]; then
    # macOS sed needs '' after -i; GNU sed doesn't. Detect and adapt.
    if sed --version >/dev/null 2>&1; then
        echo "$FILES" | xargs sed -i "s/${OLD_NAME}/${NEW_NAME}/g"
    else
        echo "$FILES" | xargs sed -i '' "s/${OLD_NAME}/${NEW_NAME}/g"
    fi
fi

echo "Done. Review changes with: git diff"
echo "Then: git add -A && git commit -m 'rename project to ${NEW_NAME}'"
