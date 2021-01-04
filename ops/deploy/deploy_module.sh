#! /bin/bash
set -e

SERVICE=$1

# Install dependencies
python -m pip install --upgrade pip
pip install -r deploy_requirements.txt

# We need gcloud beta to set up the VPC connector
gcloud components install beta

# Post-Process YAML to set up redis connections
python3 ops/deploy/postprocess_yaml.py "$SERVICE"

# Actualy run the deploy
gcloud beta app deploy "$SERVICE" --version 1 --quiet
