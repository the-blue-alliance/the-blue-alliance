#! /bin/bash
set -e

cat >./src/env_variables.yaml <<EOF
env_variables:
  FLASK_SECRET_KEY: "${FLASK_SECRET_KEY}"
EOF
