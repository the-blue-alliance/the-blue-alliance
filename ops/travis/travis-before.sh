#! /usr/bin/env sh
set -e
. $(pwd)/ops/travis/should-deploy.sh

if test "$1" != "DEPLOY" ; then
    check_clowntown_tag
fi

case "$1" in

    "PYUNIT" | "JSUNIT" | "PYBUILD" )
        echo "Setting up for unit tests..."
        paver make
        ;;
    "LINT")
        echo "Setting up to lint. Nothing to do..."
        ;;
    "DEPLOY")
        echo "Setting up to deploy. Nothing to do..."
        ;;
    *)
        echo "Unknown job type $JOB"
        exit -1
        ;;
esac
