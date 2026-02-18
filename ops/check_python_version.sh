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

# Update a file in-place with sed (portable across macOS and Linux)
update_file() {
    local file="$1"
    local pattern="$2"

    sed -i.bak "$pattern" "$file" && rm -f "$file.bak"
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
                sed -i.bak "s|requires-python = \".*\"|requires-python = \"$EXPECTED_REQUIRES_PYTHON\"|" "$PYPROJECT" && rm -f "$PYPROJECT.bak"
            else
                sed -i.bak "/^description/a\\
requires-python = \"$EXPECTED_REQUIRES_PYTHON\"" "$PYPROJECT" && rm -f "$PYPROJECT.bak"
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
