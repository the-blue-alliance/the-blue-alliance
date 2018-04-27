#! /usr/bin/env sh
. $(pwd)/ops/gcslock.sh

DEPLOY_LOCK=tbatv-prod-hrd-deploy-lock

echo "Releasing deploy lock..."
unlock $DEPLOY_LOCK
echo "Lock released. Deploy complete."
