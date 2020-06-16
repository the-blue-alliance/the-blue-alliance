#!/bin/bash

if [ "$1" == "--fix" ]
then
  black ./ --exclude '/(old_py2|stubs|subtrees|venv)/'
else
  black ./ --check --diff --exclude '/(old_py2|stubs|subtrees|venv)/'
fi
flake8 ./
