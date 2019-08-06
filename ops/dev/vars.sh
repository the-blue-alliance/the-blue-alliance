# Constants for env config
GAE_DIR=/google_appengine
NVM_DIR=/nvm
NODE_VERSION=8.16.0
NODE_DIR=${NVM_DIR}/versions/node/v${NODE_VERSION}

# First, configure environment
export PYTHONPATH="${PYTHONPATH}:${GAE_DIR}:${GAE_DIR}/lib/protorpc-1.0"
export NODE_PATH="${NODE_DIR}/lib/node_modules"
export PATH="${PATH}:${GAE_DIR}:${NODE_DIR}/bin"
