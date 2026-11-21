#!/bin/bash
# Validates that the PWA node/pnpm versions are consistent across all configuration files.
# pwa/mise.toml is the source of truth. Run this in CI to catch version drift.
#
# Usage:
#   ./check_node_versions.sh          # Check for version drift (default)
#   ./check_node_versions.sh --update # Update all files to match pwa/mise.toml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PWA_DIR="$REPO_ROOT/pwa"

UPDATE_MODE=false
if [[ "${1:-}" == "--update" || "${1:-}" == "-u" ]]; then
    UPDATE_MODE=true
fi

MISE_TOML="$PWA_DIR/mise.toml"
if [[ ! -f "$MISE_TOML" ]]; then
    echo "ERROR: mise config not found at $MISE_TOML"
    exit 1
fi

# Extract a `<tool> = "<version>"` pin from the [tools] table
mise_pin() {
    sed -n -E "s/^$1[[:space:]]*=[[:space:]]*\"([^\"]+)\".*/\1/p" "$MISE_TOML" | head -n 1
}

NODE_VERSION="$(mise_pin node)"
PNPM_VERSION="$(mise_pin pnpm)"

if [[ -z "$NODE_VERSION" || -z "$PNPM_VERSION" ]]; then
    echo "ERROR: could not read node and pnpm pins from $MISE_TOML"
    exit 1
fi

# GAE only accepts a major version (24.18.1 -> nodejs24)
GAE_RUNTIME="nodejs${NODE_VERSION%%.*}"

echo "Source of truth: node $NODE_VERSION, pnpm $PNPM_VERSION (from pwa/mise.toml)"

ERRORS=0
UPDATED=0

# check <file> <label> <current> <expected> <sed-expression>
check() {
    local file="$1" label="$2" current="$3" expected="$4" sed_expr="$5"
    local rel="${file#"$REPO_ROOT"/}"

    if [[ "$current" == "$expected" ]]; then
        echo "OK: $rel ($label)"
        return
    fi

    if [[ "$UPDATE_MODE" == true ]]; then
        sed -i.bak -E "$sed_expr" "$file" && rm -f "$file.bak"
        echo "UPDATED: $rel ($label = $expected)"
        UPDATED=$((UPDATED + 1))
    else
        echo "ERROR: $rel has $label \"$current\" (expected \"$expected\")"
        ERRORS=$((ERRORS + 1))
    fi
}

# pwa/package.json: packageManager and engines.pnpm must mirror the mise pnpm pin
PACKAGE_JSON="$PWA_DIR/package.json"
if [[ -f "$PACKAGE_JSON" ]]; then
    CURRENT_PACKAGE_MANAGER="$(sed -n -E 's/.*"packageManager"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' "$PACKAGE_JSON" | head -n 1)"
    check "$PACKAGE_JSON" "packageManager" "$CURRENT_PACKAGE_MANAGER" "pnpm@$PNPM_VERSION" \
        "s|(\"packageManager\"[[:space:]]*:[[:space:]]*\")[^\"]+\"|\1pnpm@$PNPM_VERSION\"|"

    CURRENT_ENGINES_PNPM="$(sed -n -E 's/^[[:space:]]*"pnpm"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' "$PACKAGE_JSON" | head -n 1)"
    check "$PACKAGE_JSON" "engines.pnpm" "$CURRENT_ENGINES_PNPM" "$PNPM_VERSION" \
        "s|^([[:space:]]*\"pnpm\"[[:space:]]*:[[:space:]]*\")[^\"]+\"|\1$PNPM_VERSION\"|"
fi

# GAE service configs must target the same node major version
for yaml in "$PWA_DIR"/pwa.yaml "$PWA_DIR"/pwa-preview.yaml; do
    [[ -f "$yaml" ]] || continue
    CURRENT_RUNTIME="$(sed -n -E 's/^runtime:[[:space:]]*(.+)$/\1/p' "$yaml" | head -n 1)"
    check "$yaml" "runtime" "$CURRENT_RUNTIME" "$GAE_RUNTIME" \
        "s|^runtime:[[:space:]]*nodejs[0-9]+|runtime: $GAE_RUNTIME|"
done

echo ""
if [[ "$UPDATE_MODE" == true ]]; then
    echo "Updated $UPDATED file(s) to node $NODE_VERSION / pnpm $PNPM_VERSION"
else
    if [[ $ERRORS -gt 0 ]]; then
        echo "Found $ERRORS version mismatch(es). Run with --update to fix, or update pwa/mise.toml"
        exit 1
    fi
    echo "All PWA toolchain versions are consistent!"
fi
