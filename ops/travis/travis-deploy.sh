#! /usr/bin/env sh
set -eE
. $(pwd)/ops/travis/should-deploy.sh
. $(pwd)/ops/gcslock.sh
export BOTO_CONFIG=/dev/null # Hack to fix https://github.com/travis-ci/travis-ci/issues/7940

# Deploy to GAE from travis CI
# Basically an implementation of:
# https://github.com/travis-ci/dpl/blob/master/lib/dpl/provider/gae.rb

KEYFILE=ops/$GAE_PROJECT_ID-deploy.json
PROJECT=$GAE_PROJECT_ID
VERSION=prod-2
DEPLOY_LOCK=$PROJECT-deploy-lock

BASE='https://dl.google.com/dl/cloudsdk/channels/rapid/'
NAME='google-cloud-sdk'
EXT='.tar.gz'
INSTALL=$HOME
BOOTSTRAP="$INSTALL/$NAME/bin/bootstrapping/install.py"
GCLOUD="$INSTALL/$NAME/bin/gcloud"

with_python27() {
    bash -c "source $HOME/virtualenv/python2.7/bin/activate; $1"
}

deploy_module() {
    with_python27 "$GCLOUD --quiet --verbosity warning --project $PROJECT app deploy $1 --version $VERSION"
}

deploy_full() {
  for config in app.yaml app-backend-tasks.yaml app-backend-tasks-b2.yaml api.yaml clientapi.yaml tasks.yaml cron.yaml dispatch.yaml index.yaml queue.yaml; do
    deploy_module $config
  done

  # Check if we need to deploy our Endpoints config - cleanup afterwards so it's not in our web deploy
  paver make_endpoints_config
  if check_deploy_endpoints_config; then
    with_python27 "$GCLOUD endpoints services deploy tbaMobilev9openapi.json"
  fi
  if check_deploy_tbaClient_endpoints_config; then
    with_python27 "$GCLOUD endpoints services deploy tbaClientv9openapi.json"
  fi
}

deploy_single() {
  deploy_module app.yaml
  deploy_module index.yaml
  deploy_module queue.yaml

  # Overwrite files with magic names
  mv -f ops/standalone/cron-empty.yaml ./cron.yaml
  mv -f ops/standalone/dispatch-empty.yaml ./dispatch.yaml
  deploy_module cron.yaml
  deploy_module dispatch.yaml
}

deploy_skeleton() {
  deploy_module app.yaml
  deploy_module index.yaml
  deploy_module queue.yaml

  # Overwrite files with magic names
  mv -f ops/standalone/cron-skeleton.yaml ./cron.yaml
  mv -f ops/standalone/dispatch-empty.yaml ./dispatch.yaml
  deploy_module cron.yaml
  deploy_module dispatch.yaml
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

if [ "$TBA_DEPLOY_VERBOSE" = "1" ]; then
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

echo "Obtained Lock. Deploying $PROJECT:$VERSION in mode $TBA_DEPLOY_TYPE"
case "$TBA_DEPLOY_TYPE" in
  "prod")
    deploy_full
    ;;
  "skeleton")
    deploy_skeleton
    ;;
  "single-instance")
    deploy_single
    ;;
  *)
    echo "Unknown deploy type $TBA_DEPLOY_TYPE!"
    exit -1
    ;;
esac

echo "Updating build info..."
update_build_info
