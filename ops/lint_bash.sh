#! /bin/bash
set -e

find ops -type f -iname "*.sh" -not -path "*/node_modules/*" -exec shellcheck --format=tty {} +

if ! type "shfmt" >/dev/null; then
    echo "shfmt not found"
else
    if [ "$1" == "--fix" ]; then
        find ops -type f -iname "*.sh" -not -path "*/node_modules/*" -exec shfmt -i 4 -w {} +
    else
        find ops -type f -iname "*.sh" -not -path "*/node_modules/*" -exec shfmt -i 4 -l -d {} +
    fi
fi
