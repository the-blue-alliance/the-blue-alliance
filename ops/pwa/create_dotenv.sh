#! /bin/bash
set -e

# Create .env from environment secrets if the --env flag is passed
while test $# -gt 0; do
    echo "$1"
    case "$1" in
    --env)
        touch ./pwa/.env
        cat >./pwa/.env <<EOF
VITE_TBA_API_READ_KEY="${TBA_API_READ_KEY}"
EOF
        shift
        ;;
    *)
        break
        ;;
    esac
done
