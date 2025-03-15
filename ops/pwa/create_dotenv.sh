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
VITE_FIREBASE_API_KEY="${FIREBASE_API_KEY}"
VITE_FIREBASE_AUTH_DOMAIN="${GCLOUD_PROJECT_ID}.firebaseapp.com"
VITE_FIREBASE_PROJECT_ID="${GCLOUD_PROJECT_ID}"
EOF
        shift
        ;;
    *)
        break
        ;;
    esac
done
