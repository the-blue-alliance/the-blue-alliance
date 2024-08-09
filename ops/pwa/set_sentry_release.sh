#!/bin/bash

# Install the cli
curl -sL https://sentry.io/get-cli/ | bash

VERSION=$(sentry-cli releases propose-version)

# Create a release
sentry-cli releases new "$VERSION" --org="$SENTRY_ORG" --project="$SENTRY_PROJECT" --auth-token="$SENTRY_AUTH_TOKEN"

# Associate commits with the release
sentry-cli releases set-commits "$VERSION" --auto --org="$SENTRY_ORG" --project="$SENTRY_PROJECT" --auth-token="$SENTRY_AUTH_TOKEN"

# Finalize
sentry-cli releases finalize "$VERSION" --org="$SENTRY_ORG" --project="$SENTRY_PROJECT" --auth-token="$SENTRY_AUTH_TOKEN"
