#!/bin/bash
set -e

if [ -n "$CI" ]; then
    pyrefly check --output-format full-text-with-github "$@"
else
    pyrefly check "$@"
fi
