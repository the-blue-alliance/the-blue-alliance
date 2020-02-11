#! /usr/bin/env sh
set -e
. $(pwd)/ops/travis/should-deploy.sh

if test "$1" != "DEPLOY" ; then
    check_clowntown_tag
fi

case "$1" in

    "JSUNIT" )
        echo "Setting up for unit tests..."
        npm i
        ;;
    "PYUNIT")
        echo "Setting up pyunit. Nothing to do..."
        ;;
    "PYBUILD")
        echo "Setting up pybuild. Nothing to do..."
        ;;
    "LINT")
        echo "Setting up to lint. Nothing to do..."
        ;;
    "MAKE")
        echo "Setting up to make."
        cp static/javascript/tba_js/tba_keys_template.js static/javascript/tba_js/tba_keys.js
        ;;
    "DEPLOY")
        echo "Setting up to deploy. Nothing to do..."
        ;;
    *)
        echo "Unknown job type $JOB"
        exit -1
        ;;
esac
