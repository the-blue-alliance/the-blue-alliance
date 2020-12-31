#! /usr/loca/bin/python3
import argparse
import os
import sys

import yaml


"""
This script will parse the `queue.yaml` file passed and deploy the queues via `gcloud tasks queue`.
If the queue exists, the queue will be updated. If the queue does not exist, it will be created.
Queues will not be automatically deleted - queues removed from `queue.yaml` should be deleted
in the Cloud Tasks web interface.

This script depends on pyyaml
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("queues", help="Path to `queue.yaml` file")

    args = parser.parse_args()

    with open(args.queues) as queues_file:
        queues_config = yaml.safe_load(queues_file)

    queues = queues_config.get("queue", [])

    for queue in queues:
        name = queue.get("name")
        if name is None:
            continue

        args = []

        # max_dispatches_per_second
        max_dispatches_per_second = queue.get("max_dispatches_per_second")
        if max_dispatches_per_second:
            max_dispatches_per_second = float(max_dispatches_per_second)
            args.append(f"--max-dispatches-per-second={max_dispatches_per_second}")

        # max_concurrent_dispatches
        # Cloud Taks defaults to 1000, but TBA assumes 0 if unspecified
        max_concurrent_dispatches = queue.get("max_concurrent_dispatches", 0)
        max_concurrent_dispatches = int(max_concurrent_dispatches)
        args.append(f"--max-concurrent-dispatches={max_concurrent_dispatches}")

        # max_attempts
        # Cloud Taks defaults to 100, but TBA assumes -1 if unspecified
        max_attempts = queue.get("max_attempts", -1)
        max_attempts = int(max_attempts)
        args.append(f"--max-attempts={max_attempts}")

        # max_retry_duration_seconds
        max_retry_duration_seconds = queue.get("max_retry_duration_seconds")
        if max_retry_duration_seconds:
            max_retry_duration_seconds = int(max_retry_duration_seconds)
            args.append(f"--max-retry-duration={max_retry_duration_seconds}s")

        # min_backoff_seconds
        min_backoff_seconds = queue.get("min_backoff_seconds")
        if min_backoff_seconds:
            min_backoff_seconds = int(min_backoff_seconds)
            args.append(f"--min-backoff={min_backoff_seconds}s")

        # max_backoff_seconds
        max_backoff_seconds = queue.get("max_backoff_seconds")
        if max_backoff_seconds:
            max_backoff_seconds = int(max_backoff_seconds)
            args.append(f"--max-backoff={max_backoff_seconds}s")

        # max_doublings
        max_doublings = queue.get("max_doublings")
        if max_doublings:
            max_doublings = int(max_doublings)
            args.append(f"--max-doublings={max_doublings}")

        arg_str = " ".join(args)

        # First attempt to update the queue. If that fails, attempt to create the queue.
        sub_commands = ["update", "create"]
        for sub_command in sub_commands:
            command = f"gcloud tasks queues {sub_command} {name} {arg_str}"
            print(command)
            output = os.system(command)
            if output == 0:
                break

    return 0


if __name__ == "__main__":
    sys.exit(main())
