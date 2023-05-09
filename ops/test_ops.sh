#!/bin/bash

npm run testops -- --runInBand --testTimeout=10000 --silent=false
ret=$?

if [ -n "$CI" ]; then
    ./ops/dev/pull-gae-logs.sh
    cat /tmp/tba.log
fi

exit $ret
