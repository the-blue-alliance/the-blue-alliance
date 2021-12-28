#!/bin/bash
set -e

# We simply use `pyre` over `pyre check` because this will
# allow incremental checking if watchman can be found
pyre
