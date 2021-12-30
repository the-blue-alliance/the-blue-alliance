#!/bin/bash

echo "::add-matcher::./ops/problem_matchers/flake8_error.json"
echo "::add-matcher::./ops/problem_matchers/flake8_warning.json"
if [ "$1" == "--fix" ]; then
    black ./ --exclude '/(old_py2|stubs|subtrees|venv)/'
else
    black ./ --check --diff --exclude '/(old_py2|stubs|subtrees|venv)/'
fi
flake8 ./
