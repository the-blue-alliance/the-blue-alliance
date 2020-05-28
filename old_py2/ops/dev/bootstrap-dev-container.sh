#! /bin/bash
set -e

source ops/dev/vars.sh

# Place for local datastore
mkdir -p /datastore

npm install uglify-js@2.7.0 -g --silent
npm install -g gulp-cli uglify-es uglifycss less tslib request swagger-cli --silent

pip install --upgrade -r requirements.txt

pip install --upgrade -r travis_requirements.txt
paver install_libs
npm install

# Put in a dummy keys so that paver make works
cp static/javascript/tba_js/tba_keys_template.js static/javascript/tba_js/tba_keys.js

paver make


echo "Downloading cloud sql proxy"
wget -q https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /cloud_sql_proxy
chmod +x /cloud_sql_proxy
