#! /bin/bash
set -e

source ops/dev/vars.sh
echo "Starting devserver in tmux session..."
tmux new-session -d "paver devserver; read"
