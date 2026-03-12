#! /bin/bash
set -e

# Create .env from VITE_* environment variables if the --env flag is passed
while test $# -gt 0; do
    echo "$1"
    case "$1" in
    --env)
        for var in $(compgen -e | grep '^VITE_' | sort); do
            printf '%s="%s"\n' "$var" "${!var}"
        done >./pwa/.env
        shift
        ;;
    *)
        break
        ;;
    esac
done
