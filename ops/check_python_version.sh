#!/bin/sh
# Validates that Python version is consistent across all configuration files
# Run this in CI to catch version drift
#
# Usage:
#   ./check_python_version.sh          # Check for version drift (default)
#   ./check_python_version.sh --update # Update all files to match .python-version

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

UPDATE_MODE=false
if [ "$1" = "--update" ] || [ "$1" = "-u" ]; then
    UPDATE_MODE=true
fi

# Extract Python version from .python-version (source of truth)
PYTHON_VERSION_FILE="$REPO_ROOT/.python-version"
if [ ! -f "$PYTHON_VERSION_FILE" ]; then
    echo "ERROR: .python-version file not found at $PYTHON_VERSION_FILE"
    exit 1
fi

PYTHON_VERSION=$(cat "$PYTHON_VERSION_FILE" | tr -d '[:space:]')

if [ -z "$PYTHON_VERSION" ]; then
    echo "ERROR: .python-version file is empty"
    exit 1
fi

echo "Source of truth Python version: $PYTHON_VERSION (from .python-version)"

# Convert to GAE format (3.13 -> python313)
GAE_RUNTIME="python$(echo "$PYTHON_VERSION" | tr -d '.')"

ERRORS=0
UPDATED=0

# Update a file in-place with sed
update_file() {
    _uf_file="$1"
    _uf_pattern="$2"

    sed -i "$_uf_pattern" "$_uf_file"
    echo "UPDATED: $_uf_file"
    UPDATED=$((UPDATED + 1))
}

# Check/update docker-compose.yml
COMPOSE_FILE="$REPO_ROOT/docker-compose.yml"
if [ -f "$COMPOSE_FILE" ]; then
    COMPOSE_VERSION=$(grep 'x-python-version:' "$COMPOSE_FILE" | sed 's/.*"\([0-9.]*\)".*/\1/')
    if [ "$COMPOSE_VERSION" != "$PYTHON_VERSION" ]; then
        if [ "$UPDATE_MODE" = true ]; then
            update_file "$COMPOSE_FILE" "s/x-python-version: &python-version \"[0-9.]*\"/x-python-version: \&python-version \"$PYTHON_VERSION\"/"
        else
            echo "ERROR: $COMPOSE_FILE has x-python-version: \"$COMPOSE_VERSION\" (expected \"$PYTHON_VERSION\")"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "OK: $COMPOSE_FILE"
    fi
fi

# Check/update GAE yaml files
for yaml in "$REPO_ROOT"/src/*.yaml; do
    if grep -q "^runtime:" "$yaml"; then
        RUNTIME=$(grep "^runtime:" "$yaml" | awk '{print $2}')
        if [ "$RUNTIME" != "$GAE_RUNTIME" ]; then
            if [ "$UPDATE_MODE" = true ]; then
                update_file "$yaml" "s/^runtime: python[0-9]*/runtime: $GAE_RUNTIME/"
            else
                echo "ERROR: $yaml has runtime: $RUNTIME (expected $GAE_RUNTIME)"
                ERRORS=$((ERRORS + 1))
            fi
        else
            echo "OK: $yaml"
        fi
    fi
done

# Check/update Dockerfile defaults
for dockerfile in "$REPO_ROOT"/ops/dev/docker/Dockerfile*; do
    # Handle ARG-based Python version defaults
    if grep -q "ARG PYTHON_VERSION=" "$dockerfile"; then
        DEFAULT=$(grep "ARG PYTHON_VERSION=" "$dockerfile" | sed 's/ARG PYTHON_VERSION=//')
        if [ "$DEFAULT" != "$PYTHON_VERSION" ]; then
            if [ "$UPDATE_MODE" = true ]; then
                update_file "$dockerfile" "s/ARG PYTHON_VERSION=[0-9.]*/ARG PYTHON_VERSION=$PYTHON_VERSION/"
            else
                echo "ERROR: $dockerfile has default ARG PYTHON_VERSION=$DEFAULT (expected $PYTHON_VERSION)"
                ERRORS=$((ERRORS + 1))
            fi
        else
            echo "OK: $dockerfile (ARG PYTHON_VERSION)"
        fi
    fi

    # Handle ENV-based Python version defaults (e.g., ENV PYTHON_VERSION=python3.13)
    if grep -q "ENV PYTHON_VERSION=" "$dockerfile"; then
        ENV_DEFAULT=$(grep "ENV PYTHON_VERSION=" "$dockerfile" | sed 's/ENV PYTHON_VERSION=//')
        EXPECTED_ENV_VALUE="python$PYTHON_VERSION"
        if [ "$ENV_DEFAULT" != "$EXPECTED_ENV_VALUE" ]; then
            if [ "$UPDATE_MODE" = true ]; then
                # Replace the value part of ENV PYTHON_VERSION=...
                sed -i "s|ENV PYTHON_VERSION=.*|ENV PYTHON_VERSION=$EXPECTED_ENV_VALUE|" "$dockerfile"
                echo "UPDATED: $dockerfile (ENV PYTHON_VERSION)"
                UPDATED=$((UPDATED + 1))
            else
                echo "ERROR: $dockerfile has ENV PYTHON_VERSION=$ENV_DEFAULT (expected $EXPECTED_ENV_VALUE)"
                ERRORS=$((ERRORS + 1))
            fi
        else
            echo "OK: $dockerfile (ENV PYTHON_VERSION)"
        fi
    fi
done

# Check/update GitHub Actions workflow files
for workflow in "$REPO_ROOT"/.github/workflows/*.yml; do
    if [ -f "$workflow" ]; then
        # Count mismatched python-version entries
        MISMATCHES=$(grep -E "python-version:[[:space:]]*[\"']?[0-9.]+" "$workflow" | grep -Fcv -- "$PYTHON_VERSION" || true)
        if [ "$MISMATCHES" -gt 0 ]; then
            if [ "$UPDATE_MODE" = true ]; then
                # Update all python-version entries (handles both quoted styles)
                sed -i -E "s/(python-version:[[:space:]]*[\"']?)[0-9.]+([\"']?)/\1$PYTHON_VERSION\2/g" "$workflow"
                echo "UPDATED: $workflow ($MISMATCHES occurrences)"
                UPDATED=$((UPDATED + 1))
            else
                echo "ERROR: $workflow has $MISMATCHES python-version entries not set to $PYTHON_VERSION"
                ERRORS=$((ERRORS + 1))
            fi
        else
            # Check if it has any python-version entries at all
            if grep -q "python-version:" "$workflow"; then
                echo "OK: $workflow"
            fi
        fi
    fi
done

echo ""
if [ "$UPDATE_MODE" = true ]; then
    echo "Updated $UPDATED file(s) to Python $PYTHON_VERSION"
else
    if [ $ERRORS -gt 0 ]; then
        echo "Found $ERRORS version mismatch(es). Run with --update to fix, or update .python-version"
        exit 1
    fi
    echo "All Python versions are consistent!"
fi
