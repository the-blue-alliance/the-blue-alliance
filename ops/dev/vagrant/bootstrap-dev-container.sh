#! /bin/bash
set -e

# Place for local datastore
mkdir -p /datastore

# nodejs dependencies
npm install uglify-js  --silent
npm install -g npx gulp-cli uglify-es uglifycss less tslib request swagger-cli --silent


./ops/build/run_buildweb.sh
