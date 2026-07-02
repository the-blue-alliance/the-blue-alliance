#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

import re
import subprocess
import sys
import time

import requests

TIME_LIMIT = 10 * 60  # seconds
HOMEPAGE_URL = "http://localhost:8080"
MODULE_NAMES = {
    "default",
    "py3-web",
    "py3-api",
    "py3-tasks-io",
    "py3-tasks-cpu-enqueue",
    "py3-tasks-cpu",
}

# Wait up to |TIME_LIMIT| for all services to start
start_time = time.time()
while time.time() - start_time < TIME_LIMIT:
    # Check for started modules
    result = subprocess.run(
        ["docker", "compose", "logs", "tba"], capture_output=True, text=True
    )
    started = set(re.findall(r'Starting module "(.*)"', result.stdout))
    not_started = MODULE_NAMES.difference(started)
    if not_started:
        print(f"Not started modules: {not_started}")
        time.sleep(5)
        continue
    print(f"Started modules: {started}")

    # Check for webpack build
    result = subprocess.run(
        ["docker", "compose", "logs", "webpack"], capture_output=True, text=True
    )
    m = re.search(
        r"webpack .* compiled successfully in .*", result.stdout + result.stderr
    )
    if not m:
        print("Webpack not compiled")
        time.sleep(5)
        continue
    print(m.group(0))

    # Check that homepage returns a 200
    try:
        r = requests.get(HOMEPAGE_URL, timeout=5)
        print(f"Homepage: {r.status_code}")
        if r.status_code == 200:
            print("Startup successful!")
            sys.exit(0)
    except (requests.ConnectionError, requests.Timeout):
        print("Homepage not ready")
        time.sleep(5)
        continue

print("Fail: Didn't start up in time")
container_logs = subprocess.run(
    ["docker", "compose", "logs", "tba"], capture_output=True, text=True
)
print(f"Container Logs:\n{container_logs.stdout}")
sys.exit(1)
