#!/bin/bash

# Install the cli
curl -sL https://sentry.io/get-cli/ | bash

VERSION="sentry-cli releases propose-version"

# Create a release
sentry-cli releases new "$VERSION"

# Associate commits with the release
sentry-cli releases set-commits "$VERSION" --auto

# Finalize
sentry-cli releases finalize "$VERSION"
