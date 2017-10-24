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

paver make
