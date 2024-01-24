#! /bin/bash
set -e

gcloud app deploy src/dispatch.yaml --version prod-2 --quiet
