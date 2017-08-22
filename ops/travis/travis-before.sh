#! /usr/bin/env sh
set -e

case "$1" in

    "PYUNIT" | "PYLINT" | "JSUNIT" | "JSLINT")
        echo "Setting up for unit tests..."
        paver make
        ;;
    "DEPLOY")
        echo "Setting up to deploy. Nothing to do..."
        ;;
    *)
        echo "Unknown job type $JOB"
        exit -1
        ;;
esac
