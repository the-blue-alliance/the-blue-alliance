#! /usr/bin/env sh
set -e
. $(pwd)/ops/travis/should-deploy.sh

# Deploy to GAE from travis CI
# Basically an implementation of:
# https://github.com/travis-ci/dpl/blob/master/lib/dpl/provider/gae.rb

KEYFILE=ops/tbatv-prod-hrd-deploy.json
PROJECT=tbatv-prod-hrd
VERSION=prod-1

BASE='https://dl.google.com/dl/cloudsdk/channels/rapid/'
NAME='google-cloud-sdk'
EXT='.tar.gz'
INSTALL=$HOME
BOOTSTRAP="$INSTALL/$NAME/bin/bootstrapping/install.py"
GCLOUD="$INSTALL/$NAME/bin/gcloud"

with_python27() {
    bash -c "source $HOME/virtualenv/python2.7/bin/activate; $1"
}

should_deploy

echo "python 2.7 version:"
with_python27 "python -c 'import sys; print(sys.version)'"

echo "Downloading Google Cloud SDK ..."
curl -L "${BASE}${NAME}${EXT}" | gzip -d | tar -x -C ${INSTALL}

echo "Bootstrapping Google Cloud SDK ..."
with_python27 "$BOOTSTRAP --usage-reporting=false --command-completion=false --path-update=false"

echo "Building TBA..."
paver make

echo "Configuring service account auth..."
with_python27 "$GCLOUD -q auth activate-service-account --key-file $KEYFILE"

echo "Deploying $PROJECT:$VERSION"
# need more permissiosn for cron.yaml queue.yaml index.yaml, we can come back to them
for config in dispatch.yaml app.yaml app-backend-tasks.yaml app-backend-tasks-b2.yaml; do
    with_python27 "$GCLOUD --quiet --verbosity warning --project $PROJECT app deploy $config --version $VERSION"
done
