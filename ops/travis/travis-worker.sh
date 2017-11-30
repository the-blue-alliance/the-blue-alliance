#! /usr/bin/env sh
set -e
. $(pwd)/ops/travis/should-deploy.sh

if test "$1" != "DEPLOY" ; then
    check_clowntown_tag
fi

case "$1" in

    "PYUNIT")
        echo "Running python unit tests"
        paver test
        ;;
    "LINT")
	echo "Linting python..."
        if test "$TRAVIS_BRANCH" != "" ; then
            echo "Linting all changes between HEAD and $TRAVIS_BRANCH"
            paver lint --base $TRAVIS_BRANCH
        else
            echo "Linting all current changes"
            paver lint
        fi

        # Lint Javascript
	echo "Linting javascript..."
        npm run lint -s

	# Lint swagger files
	echo "Linting swagger specs..."
	find $(pwd)/static/swagger -type f -name "*.json" | xargs -n 1 swagger-cli validate
        ;;
    "PYBUILD")
        echo "Building all python files"
        python -m compileall -f -q -x ".*/(node_modules|lib|subtrees)/.*" .
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
