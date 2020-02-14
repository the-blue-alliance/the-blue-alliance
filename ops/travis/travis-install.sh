#! /usr/bin/env sh
set -e
. $(pwd)/ops/travis/should-deploy.sh

if [ "$TRAVIS" = "true" -a "$TRAVIS_EVENT_TYPE" = "pull_request" -a "$1" = "DEPLOY" ] ; then
    echo "No deploys on pull requests, skipping travis_before"
    exit 0
fi

if test "$1" = "DEPLOY" ; then
    should_deploy
else
    check_clowntown_tag
fi

pip install -r travis_requirements.txt
paver install_libs
GAE_VERSION="1.9.66"
wget https://storage.googleapis.com/appengine-sdks/featured/google_appengine_$GAE_VERSION.zip -nv
unzip -q google_appengine_$GAE_VERSION.zip -d $HOME
rm google_appengine_$GAE_VERSION.zip
npm install
npm install -g gulp-cli uglify-es uglifycss less request tslib
npm ls || true
