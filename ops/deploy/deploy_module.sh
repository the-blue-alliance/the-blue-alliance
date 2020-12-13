#! /bin/bash
set -e

SERVICE=$1

# Post-Process YAML to set up redis connections
python3 ops/deploy/postprocess_yaml.py "$SERVICE"

gcloud beta app deploy "$SERVICE" --version 1 --quiet
