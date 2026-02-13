#!/bin/bash
set -e

# Detect the site-packages path so ty can find installed third-party packages
SITE_PACKAGES=$(python3 -c "import sysconfig; print(sysconfig.get_path('purelib'))")

if [ -n "$CI" ]; then
    ty check --extra-search-path "$SITE_PACKAGES" --output-format github src/ ops/
else
    ty check --extra-search-path "$SITE_PACKAGES" src/ ops/
fi
