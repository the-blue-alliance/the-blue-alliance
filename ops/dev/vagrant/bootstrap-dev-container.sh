#! /bin/bash
set -e

# Place for local datastore
mkdir -p /datastore

# The datastore emulator requires grpcio
pip2 install grpcio
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r src/requirements.txt

# nodejs dependencies
npm install uglify-js --silent
npm install -g npx gulp-cli uglify-es uglifycss less tslib request swagger-cli --silent


./ops/build/run_buildweb.sh
