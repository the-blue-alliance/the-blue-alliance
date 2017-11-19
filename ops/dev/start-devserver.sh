#! /bin/bash
set -e

source ops/dev/vars.sh
session=tba
tmux start-server

if tmux has-session -t $session ; then
    echo "Found existing session. Killing and recreating..."
    tmux kill-session -t $session
fi

echo "Starting devserver in new tmux session..."
tmux new-session -d -s $session
tmux new-window -t "$session:1" -n gae "paver devserver 2>&1 | tee /var/log/tba.log; read"
tmux new-window -t "$session:2" -n gulp "gulp; read"
tmux select-window -t "$session:0"

tmux list-sessions
tmux list-windows
