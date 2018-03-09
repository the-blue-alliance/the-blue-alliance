#! /bin/bash
set -e

source ops/dev/vars.sh
session=tba
tmux start-server

if tmux has-session -t $session ; then
    echo "Found existing session. Killing and recreating..."
    tmux kill-session -t $session
fi

instance_name=""
auth_path=""
if [ -f /ops/dev/conf.json ] ; then
  instance_name=$(cat ops/dev/conf.json | jq .cloud_sql_instance | jq -r 'select(type == "string")')
  auth_path=$(cat ops/dev/conf.json | jq .auth_file | jq -r 'select(type == "string")')
fi

echo "Starting devserver in new tmux session..."
tmux new-session -d -s $session
tmux new-window -t "$session:1" -n gae "paver devserver 2>&1 | tee /var/log/tba.log; read"
tmux new-window -t "$session:2" -n gulp "gulp; read"
if [ ! -z "$instance_name" ]; then
  echo "Starting Cloud SQL proxy to connect to $instance_name"
  tmux new-window -t "$session:3" -n sql "/cloud_sql_proxy -instances=$instance_name=tcp:3306 -credential_file=$auth_path | tee /var/log/sql.log; read"
fi
tmux select-window -t "$session:1"

tmux list-sessions
tmux list-windows
