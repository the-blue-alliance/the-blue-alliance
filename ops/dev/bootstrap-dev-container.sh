#! /bin/bash
set -e

source ops/dev/vars.sh

npm install uglify-js@2.7.0 -g --silent
npm install -g gulp-cli uglify-es uglifycss less request --silent

pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip install --upgrade -r travis_requirements.txt -t lib
paver install_libs
npm install

# Put in a dummy keys so that paver make works
mv static/javascript/tba_js/tba_keys_template.js static/javascript/tba_js/tba_keys.js

paver make
