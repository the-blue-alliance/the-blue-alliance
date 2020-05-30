set -e

GCLOUD_PROJECT=${GCLOUD_PROJECT:-tbatv-prod-hrd}

cd ops/dev
gcloud --project $GCLOUD_PROJECT builds submit . --config=cloudbuild.yaml
