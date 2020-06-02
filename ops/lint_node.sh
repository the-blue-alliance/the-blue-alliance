#!/bin/bash

if [ "$1" == "--fix" ]
then
  npm run lintfix
else
  npm run lint
fi
