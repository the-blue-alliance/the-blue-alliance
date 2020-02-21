#! /usr/bin/env sh
set -eE
. $(pwd)/ops/travis/should-deploy.sh
. $(pwd)/ops/gcslock.sh
export BOTO_CONFIG=/dev/null # Hack to fix https://github.com/travis-ci/travis-ci/issues/7940

# Deploy to GAE from travis CI
# Basically an implementation of:
# https://github.com/travis-ci/dpl/blob/master/lib/dpl/provider/gae.rb

KEYFILE=ops/tbatv-prod-hrd-deploy.json
PROJECT=tbatv-prod-hrd
VERSION=prod-2
DEPLOY_LOCK=tbatv-prod-hrd-deploy-lock

BASE='https://dl.google.com/dl/cloudsdk/channels/rapid/'
NAME='google-cloud-sdk'
EXT='.tar.gz'
INSTALL=$HOME
BOOTSTRAP="$INSTALL/$NAME/bin/bootstrapping/install.py"
GCLOUD="$INSTALL/$NAME/bin/gcloud"

with_python27() {
    bash -c "source $HOME/virtualenv/python2.7/bin/activate; $1"
}

# Install the lock release function as a trap so it always runs
# http://tldp.org/LDP/Bash-Beginners-Guide/html/sect_12_02.html
release_lock() {
  echo "Releasing deploy lock..."
  unlock $DEPLOY_LOCK
  echo "Lock released. Deploy complete."
}

should_deploy

echo "python 2.7 version:"
with_python27 "python -c 'import sys; print(sys.version)'"

echo "Downloading Google Cloud SDK ..."
curl -L "${BASE}${NAME}${EXT}" | gzip -d | tar -x -C ${INSTALL}

echo "Bootstrapping Google Cloud SDK ..."
with_python27 "$BOOTSTRAP --usage-reporting=false --command-completion=false --path-update=false"

PATH=$PATH:$INSTALL/$NAME/bin/

echo "Building TBA..."
paver make

if [ "$TBA_DEPLOY_VERBOSE" = "1"]; then
  echo "Deploying TBA with the following JS modules"
  npm ls || true
fi

echo "Configuring service account auth..."
with_python27 "$GCLOUD -q auth activate-service-account --key-file $KEYFILE"

echo "Obtaining deploy lock..."
lock $DEPLOY_LOCK

# Now that we have the lock, always try to release it when this script exits
echo "Installing trap handler to release deploy lock on exit..."
trap release_lock EXIT INT TERM

echo "Obtained Lock. Deploying $PROJECT:$VERSION"
for config in app.yaml app-backend-tasks.yaml app-backend-tasks-b2.yaml api.yaml clientapi.yaml tasks.yaml cron.yaml dispatch.yaml index.yaml queue.yaml; do
    with_python27 "$GCLOUD --quiet --verbosity warning --project $PROJECT app deploy $config --version $VERSION"
done

# Check if we need to deploy our Endpoints config - cleanup afterwards so it's not in our web deploy
paver make_endpoints_config
if check_deploy_endpoints_config; then
  with_python27 "$GCLOUD endpoints services deploy tbaMobilev9openapi.json"
fi
if check_deploy_tbaClient_endpoints_config; then
  with_python27 "$GCLOUD endpoints services deploy tbaClientv9openapi.json"
fi

echo "Updating build info..."
update_build_info
