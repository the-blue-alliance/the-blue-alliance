#!/bin/bash

declare -a cmds=("vagrant rsync-auto" "./ops/dev/print-gae-logs.sh")
for cmd in "${cmds[@]}"; do {
  echo "Running $cmd"
  $cmd & pid=$!
  PID_LIST+=" $pid";
} done

trap "kill $PID_LIST" SIGINT

wait $PID_LIST

echo
echo "All processes have completed";
