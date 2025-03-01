#! /bin/bash
set -e

SERVICE=$1

gcloud app deploy "$SERVICE" --version 1 --quiet
