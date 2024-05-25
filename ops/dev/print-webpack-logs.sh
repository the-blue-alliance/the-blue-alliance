#! /bin/bash
set -e

vagrant ssh -- -t 'tail -f /var/log/webpack.log'
