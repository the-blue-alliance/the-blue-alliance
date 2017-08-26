#! /usr/bin/env sh
set -e

case "$1" in

    "PYUNIT")
        echo "Running python unit tests"
        paver test
        ;;
    "LINT")
        if test "$TRAVIS" == "true" && "$TRAVIS_EVENT_TYPE" != "pull_request" ; then
            echo "Lint should only run on pull request builds"
            exit 0
        fi

        if test "$TRAVIS_BRANCH" != "" ; then
            echo "Linting all changes between HEAD and $TRAVIS_BRANCH"
            paver lint --base $TRAVIS_BRANCH
        else
            echo "Linting all current changes"
            paver lint
        fi

        # Lint Javascript
        npm run lint -s
        ;;
    "PYBUILD")
        echo "Building all python files"
        python -m compileall .
        ;;
    "JSUNIT")
        echo "Running javascript tests"
        npm test
        ;;
    *)
        echo "Unknown job type $JOB"
        exit -1
        ;;
esac
