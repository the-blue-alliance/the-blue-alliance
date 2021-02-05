#! /bin/bash
set -e

find ops -type f -iname "*.sh" -exec shellcheck --format=tty {} +

if ! type "shfmt" >/dev/null; then
    echo "shfmt not found, install from https://github.com/mvdan/sh to use"
else
    shfmt -i 4 -l -d ops/
fi
