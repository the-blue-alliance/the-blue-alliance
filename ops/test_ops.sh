#!/bin/bash

npm run testops
ret=$?

if [ -n "$CI" ]; then
    ./ops/dev/pull-gae-logs.sh
    cat /tmp/tba.log
fi

exit $ret
