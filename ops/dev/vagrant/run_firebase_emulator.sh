#!/bin/bash -i
set -e

source ops/dev/vagrant/config.sh

PROJECT_ID=$(project)
export PROJECT_ID

cd ops/dev/firebase
npm i

./start.sh
