#!/bin/bash
# Validates that Python version is consistent across all configuration files
# Run this in CI to catch version drift
#
# Usage:
#   ./check_python_version.sh          # Check for version drift (default)
#   ./check_python_version.sh --update # Update all files to match .python-version

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

UPDATE_MODE=false
if [[ "${1:-}" == "--update" || "${1:-}" == "-u" ]]; then
    UPDATE_MODE=true
fi

# Extract Python version from .python-version (source of truth)
PYTHON_VERSION_FILE="$REPO_ROOT/.python-version"
if [[ ! -f "$PYTHON_VERSION_FILE" ]]; then
    echo "ERROR: .python-version file not found at $PYTHON_VERSION_FILE"
    exit 1
fi

PYTHON_VERSION=$(tr -d '[:space:]' <"$PYTHON_VERSION_FILE")

if [[ -z "$PYTHON_VERSION" ]]; then
    echo "ERROR: .python-version file is empty"
    exit 1
fi

echo "Source of truth Python version: $PYTHON_VERSION (from .python-version)"

# Convert to GAE format (3.13 -> python313)
GAE_RUNTIME="python${PYTHON_VERSION//./}"

ERRORS=0
UPDATED=0

# Update a file in-place with sed
update_file() {
    local file="$1"
    local pattern="$2"

    sed -i '' "$pattern" "$file"
    echo "UPDATED: $file"
    UPDATED=$((UPDATED + 1))
}

# Check/update requires-python in pyproject.toml
PYPROJECT="$REPO_ROOT/pyproject.toml"
if [[ -f "$PYPROJECT" ]]; then
    EXPECTED_REQUIRES_PYTHON=">=${PYTHON_VERSION}"
    CURRENT_REQUIRES_PYTHON=$(grep 'requires-python' "$PYPROJECT" | sed 's/.*"\(.*\)".*/\1/' || true)
    if [[ "$CURRENT_REQUIRES_PYTHON" != "$EXPECTED_REQUIRES_PYTHON" ]]; then
        if [[ "$UPDATE_MODE" == true ]]; then
            if grep -q 'requires-python' "$PYPROJECT"; then
                sed -i '' "s|requires-python = \".*\"|requires-python = \"$EXPECTED_REQUIRES_PYTHON\"|" "$PYPROJECT"
            else
                sed -i '' "/^description/a\\
requires-python = \"$EXPECTED_REQUIRES_PYTHON\"" "$PYPROJECT"
            fi
            echo "UPDATED: $PYPROJECT (requires-python = \"$EXPECTED_REQUIRES_PYTHON\")"
            UPDATED=$((UPDATED + 1))
        else
            echo "ERROR: $PYPROJECT has requires-python = \"$CURRENT_REQUIRES_PYTHON\" (expected \"$EXPECTED_REQUIRES_PYTHON\")"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "OK: $PYPROJECT (requires-python)"
    fi
fi

# Check/update GAE yaml files
for yaml in "$REPO_ROOT"/src/*.yaml; do
    if grep -q "^runtime:" "$yaml"; then
        RUNTIME=$(grep "^runtime:" "$yaml" | awk '{print $2}')
        if [[ "$RUNTIME" != "$GAE_RUNTIME" ]]; then
            if [[ "$UPDATE_MODE" == true ]]; then
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
        local_default=$(grep "ARG PYTHON_VERSION=" "$dockerfile" | sed 's/ARG PYTHON_VERSION=//')
        if [[ "$local_default" != "$PYTHON_VERSION" ]]; then
            if [[ "$UPDATE_MODE" == true ]]; then
                update_file "$dockerfile" "s/ARG PYTHON_VERSION=[0-9.]*/ARG PYTHON_VERSION=$PYTHON_VERSION/"
            else
                echo "ERROR: $dockerfile has default ARG PYTHON_VERSION=$local_default (expected $PYTHON_VERSION)"
                ERRORS=$((ERRORS + 1))
            fi
        else
            echo "OK: $dockerfile (ARG PYTHON_VERSION)"
        fi
    fi

    # Handle ENV-based Python version defaults (e.g., ENV PYTHON_VERSION=python3.13)
    if grep -q "ENV PYTHON_VERSION=" "$dockerfile"; then
        local_env_default=$(grep "ENV PYTHON_VERSION=" "$dockerfile" | sed 's/ENV PYTHON_VERSION=//')
        local_expected_env_value="python$PYTHON_VERSION"
        if [[ "$local_env_default" != "$local_expected_env_value" ]]; then
            if [[ "$UPDATE_MODE" == true ]]; then
                sed -i '' "s|ENV PYTHON_VERSION=.*|ENV PYTHON_VERSION=$local_expected_env_value|" "$dockerfile"
                echo "UPDATED: $dockerfile (ENV PYTHON_VERSION)"
                UPDATED=$((UPDATED + 1))
            else
                echo "ERROR: $dockerfile has ENV PYTHON_VERSION=$local_env_default (expected $local_expected_env_value)"
                ERRORS=$((ERRORS + 1))
            fi
        else
            echo "OK: $dockerfile (ENV PYTHON_VERSION)"
        fi
    fi
done

# Check/update GitHub Actions workflow files
for workflow in "$REPO_ROOT"/.github/workflows/*.yml; do
    if [[ -f "$workflow" ]]; then
        # Count mismatched python-version entries
        MISMATCHES=$(grep -E "python-version:[[:space:]]*[\"']?[0-9.]+" "$workflow" | grep -Fcv -- "$PYTHON_VERSION" || true)
        if [[ "$MISMATCHES" -gt 0 ]]; then
            if [[ "$UPDATE_MODE" == true ]]; then
                # Update all python-version entries (handles both quoted styles)
                sed -i '' -E "s/(python-version:[[:space:]]*[\"']?)[0-9.]+([\"']?)/\1$PYTHON_VERSION\2/g" "$workflow"
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
if [[ "$UPDATE_MODE" == true ]]; then
    echo "Updated $UPDATED file(s) to Python $PYTHON_VERSION"
else
    if [[ $ERRORS -gt 0 ]]; then
        echo "Found $ERRORS version mismatch(es). Run with --update to fix, or update .python-version"
        exit 1
    fi
    echo "All Python versions are consistent!"
fi
