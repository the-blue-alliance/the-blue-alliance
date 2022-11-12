#! /bin/bash
set -e

# Figure out how to not run this every time
./ops/dev/vagrant/bootstrap-dev-container.sh

./ops/dev/vagrant/start-devserver.sh

exec "$@"
