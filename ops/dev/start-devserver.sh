#! /bin/bash
set -e

source ops/dev/vars.sh
echo "Starting devserver in tmux session..."
tmux start-server
tmux new-session -d -s tba
tmux new-window -t "tba:1" -n gae "paver devserver; read"
tmux new-window -t "tba:2" -n gulp "gulp; read"
tmux select-window -t "tba:0"

tmux list-sessions
tmux list-windows
