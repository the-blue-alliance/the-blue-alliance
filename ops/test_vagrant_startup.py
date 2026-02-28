#!/usr/bin/env python
import re
import subprocess
import sys
import time

import requests

TIME_LIMIT = 10 * 60  # seconds
MODULE_NAMES = {
    "default",
    "py3-web",
    "py3-api",
    "py3-tasks-io",
    "py3-tasks-cpu-enqueue",
    "py3-tasks-cpu",
}

# Check vagrant status first
print("Checking Vagrant status...", flush=True)
status_result = subprocess.run(
    ["vagrant", "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
)
print(f"Vagrant status output:\n{status_result.stdout.decode('utf-8')}", flush=True)
if status_result.returncode != 0:
    print(f"Vagrant status stderr:\n{status_result.stderr.decode('utf-8')}", flush=True)

# Test SSH connection
print("\nTesting SSH connection...", flush=True)
ssh_test = subprocess.run(
    ["vagrant", "ssh", "--", "-t", "echo 'SSH connection works'"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    timeout=30,
)
print(f"SSH test return code: {ssh_test.returncode}", flush=True)
print(f"SSH test stdout: {repr(ssh_test.stdout.decode('utf-8'))}", flush=True)
print(f"SSH test stderr: {repr(ssh_test.stderr.decode('utf-8'))}", flush=True)

# Check if bootstrap completed
print("\nChecking if bootstrap completed...", flush=True)
bootstrap_check = subprocess.run(
    ["vagrant", "ssh", "--", "-t", "ls -la /tba/src/build/ | head -5"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    timeout=30,
)
print(f"Build dir check: {bootstrap_check.stdout.decode('utf-8')}", flush=True)

# Check for any provisioning errors
print("\nChecking for provisioning issues...", flush=True)
provision_check = subprocess.run(
    [
        "vagrant",
        "ssh",
        "--",
        "-t",
        "ps aux | grep -E '(dev_appserver|tmux)' | grep -v grep",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    timeout=30,
)
print(f"Process check:\n{provision_check.stdout.decode('utf-8')}", flush=True)

# Wait up to |TIME_LIMIT| for all modules to start and webpack to build
start_time = time.time()
iteration = 0
while time.time() - start_time < TIME_LIMIT:
    iteration += 1
    print(
        f"\n=== Iteration {iteration} (elapsed: {int(time.time() - start_time)}s) ===",
        flush=True,
    )

    # Check if tmux session is running
    print("Checking tmux session...", flush=True)
    tmux_check = subprocess.run(
        ["vagrant", "ssh", "--", "-t", "tmux list-windows -t tba"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    if tmux_check.returncode == 0:
        print(f"Tmux windows:\n{tmux_check.stdout.decode('utf-8')}", flush=True)
    else:
        print(
            f"Tmux not running or error: {tmux_check.stderr.decode('utf-8')}",
            flush=True,
        )

    # Check for started modules
    print("Checking GAE modules...", flush=True)
    result = subprocess.run(
        ["vagrant", "ssh", "--", "-t", "cat /var/log/tba.log"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    print(f"tba.log read return code: {result.returncode}", flush=True)
    if result.returncode != 0:
        print(f"tba.log read stderr: {repr(result.stderr.decode('utf-8'))}", flush=True)
        time.sleep(5)
        continue

    tba_log_content = result.stdout.decode("utf-8")
    print(f"tba.log lines: {len(tba_log_content.splitlines())}", flush=True)

    # Show last 20 lines of tba.log for debugging
    log_lines = tba_log_content.splitlines()
    if log_lines:
        print("Last 20 lines of tba.log:", flush=True)
        for line in log_lines[-20:]:
            print(f"  {line}", flush=True)

    started = set(re.findall(r"Starting module \"(.*)\"", tba_log_content))
    not_started = MODULE_NAMES.difference(started)
    if not_started:
        print(f"Not started modules: {not_started}", flush=True)

        # Check if there are errors in the log
        error_lines = [
            line
            for line in log_lines
            if "error" in line.lower() or "exception" in line.lower()
        ]
        if error_lines:
            print(f"Found {len(error_lines)} error/exception lines:", flush=True)
            for line in error_lines[-10:]:
                print(f"  ERROR: {line}", flush=True)

        time.sleep(5)
        continue
    print(f"Started modules: {started}", flush=True)

    # Check for webpack build
    print("Checking webpack log...", flush=True)
    result = subprocess.run(
        ["vagrant", "ssh", "--", "-t", "cat /var/log/webpack.log"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    webpack_log = result.stdout.decode("utf-8")
    webpack_err = result.stderr.decode("utf-8")
    print(f"Webpack log content: {repr(webpack_log)}", flush=True)
    print(f"Webpack log stderr: {repr(webpack_err)}", flush=True)
    print(f"Webpack log return code: {result.returncode}", flush=True)

    # Check if CI variable is set in container
    ci_check = subprocess.run(
        ["vagrant", "ssh", "--", "-t", "echo CI=$CI"],
        stdout=subprocess.PIPE,
        timeout=30,
    )
    print(f"CI env in container: {ci_check.stdout.decode('utf-8').strip()}", flush=True)

    m = re.search(r"webpack .* compiled successfully in .*", webpack_log)
    if not m:
        print("Webpack not compiled - pattern not found", flush=True)
        time.sleep(5)
        continue
    print(f"Webpack compiled: {m.group(0)}", flush=True)

    # Check that homepage returns a 200
    print("Checking homepage...", flush=True)
    url = "http://localhost:8080"
    r = requests.get(url)
    print(f"Status code: {r.status_code}")
    if r.status_code == 200:
        print("Startup successful!")
        sys.exit(0)

print("Fail: Didn't start up in time")
container_logs = subprocess.run(
    ["vagrant", "ssh", "--", "-t", "cat /var/log/tba.log"], stdout=subprocess.PIPE
)
print(f"Container Logs:\n{container_logs.stdout.decode()}")
sys.exit(1)
