#! /bin/bash
set -e

source ops/dev/vars.sh

# Place for local datastore
mkdir -p /datastore

# nodejs dependencies
npm install uglify-js  --silent
npm install -g npx gulp-cli uglify-es uglifycss less tslib request swagger-cli --silent


./ops/run_buildweb.sh
