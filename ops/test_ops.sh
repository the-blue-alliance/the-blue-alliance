#!/bin/bash

npm run testops -- --runInBand --silent=false
ret=$?

if [ -n "$CI" ]; then
    docker compose logs tba
fi

exit $ret
