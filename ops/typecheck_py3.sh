#!/bin/bash
set -e

if ! command -v watchman &> /dev/null
then
    pyre check
else
    pyre incremental
fi
