#!/bin/bash
set -e

if [ -n "$CI" ]; then
    echo "::add-matcher::./ops/problem_matchers/pyre_error.json"
fi

if ! command -v watchman &>/dev/null; then
    pyre --version none check
else
    pyre --version none incremental
fi
