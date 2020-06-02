#!/bin/bash

if [ "$1" == "--fix" ]
then
  black ./src/
else
  black --check --diff ./src/
fi
flake8 ./src/
