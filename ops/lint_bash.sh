#! /bin/bash

find ops -type f -iname "*.sh" -exec shellcheck --format=tty {} +
