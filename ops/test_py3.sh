#!/bin/bash

if [ "$1" == "--relevant" ] ; then
  pytest --testmon --suppress-no-test-exit-code src
elif [ "$#" -ge 0 ] ; then
  pytest src -k "$@"
else
  pytest src --cov-report=xml --cov=src
fi
