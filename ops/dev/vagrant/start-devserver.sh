#! /bin/bash
set -e

session=tba
tmux start-server

if tmux has-session -t $session ; then
    echo "Found existing session. Killing and recreating..."
    tmux kill-session -t $session
fi

instance_name=""
auth_path=""
if [ -f /ops/dev/conf.json ] ; then
  instance_name=$(jq -r '.cloud_sql_instance | select(type == "string")'< ops/dev/conf.json)
  auth_path=$(jq -r '.auth_file | select(type == "string")' < ops/dev/conf.json)
fi

echo "Starting devserver in new tmux session..."
tmux new-session -d -s $session
tmux new-window -t "$session:1" -n gae "./ops/dev/vagrant/dev_appserver.sh 2>&1 | tee /var/log/tba.log; read"
tmux new-window -t "$session:2" -n gulp "gulp 2>&1 | tee /var/log/gulp.log; read"
tmux new-window -t "$session:3" -n redis "redis-server 2>&1 | tee /var/log/redis.log; read"
tmux new-window -t "$session:4" -n rq-worker "rq worker 2>&1 | tee /var/log/rq-worker.log; read"
tmux new-window -t "$session:5" -n rq-dashboard "rq-dashboard 2>&1 | tee /var/log/rq-dashboard.log; read"
if [ -n "$instance_name" ]; then
  echo "Starting Cloud SQL proxy to connect to $instance_name"
  tmux new-window -t "$session:6" -n sql "/cloud_sql_proxy -instances=$instance_name=tcp:3306 -credential_file=$auth_path | tee /var/log/sql.log; read"
fi
tmux select-window -t "$session:1"

tmux list-sessions
tmux list-windows

echo "To view logs and auto-update files, run \`./ops/dev/host.sh\`"
