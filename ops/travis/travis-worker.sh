#! /usr/bin/env sh
set -e

case "$1" in

    "PYUNIT")
        echo "Running python unit tests"
        paver test
        ;;
    "PYLINT")
        echo "TODO: Run flake8"
        ;;
    "JSUNIT")
        echo "Running javascript tests"
        npm test
        ;;
    "JSLINT")
        echo "Running javascript lint"
        npm run lint -s
        ;;
    *)
        echo "Unknown job type $JOB"
        exit -1
        ;;
esac
