#!/bin/bash
set -e

echo "::add-matcher::./ops/problem_matchers/pyre_error.json"
if ! command -v watchman &>/dev/null; then
    pyre check
else
    pyre incremental
fi
