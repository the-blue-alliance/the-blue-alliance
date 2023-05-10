#! /bin/bash
set -e

# TODO: Maybe figure out how to not run this every time, since it's slow
# and we don't need to do it every time
./ops/dev/vagrant/bootstrap-dev-container.sh

./ops/dev/vagrant/start-devserver.sh

exec "$@"
