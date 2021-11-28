#! /bin/bash
set -e

SERVICE=$1

# Install dependencies
python -m pip install --upgrade pip

# We need gcloud beta to set up the VPC connector
gcloud components install beta

# Actualy run the deploy
gcloud beta app deploy "$SERVICE" --version 1 --quiet
