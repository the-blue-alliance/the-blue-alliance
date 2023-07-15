#! /bin/bash
set -e

# This needs to exist for as long as we stil need to support routing for the py2 instance
# once that's gone, we can remove this, and simply deploy based on src/dispatch.yaml
# Until then, this is the same command + version from the old py2 deploy step
# https://github.com/the-blue-alliance/the-blue-alliance/blob/3dafb6697bd9d5511afaf7240eab733bd11b26a6/.github/workflows/push_py2.yml#L196C14-L196C70

mv ops/prod_dispatch.yaml src/dispatch.yaml
gcloud app deploy src/dispatch.yaml --version prod-2 --quiet
