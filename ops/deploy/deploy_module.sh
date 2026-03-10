#! /bin/bash
set -e

SERVICE=$1

# Generate src/requirements.txt from pyproject.toml for GAE deployment
# GAE Standard automatically installs requirements.txt from the app directory
if [[ "$SERVICE" == src/*.yaml ]]; then
    echo "Generating src/requirements.txt from pyproject.toml..."
    uv export --no-dev --no-hashes --frozen -o src/requirements.txt
fi

# Bake the current commit SHA into the deploy for version tracking
git rev-parse HEAD > src/COMMIT

gcloud app deploy "$SERVICE" --version 1 --quiet
