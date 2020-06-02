#!/bin/bash

if [ "$1" == "--relevant" ]
then
  pytest --testmon --suppress-no-test-exit-code src
else
  pytest src --cov-report=xml --cov=src
fi
