import argparse
import logging
import sys
from urllib.request import urlopen


def check_sdk() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("min_version")
    args = parser.parse_args()

    min_version = tuple(map(int, (args.min_version.split("."))))
    running_version = (0, 0, 0)

    try:
        with urlopen("http://localhost:8080/local/sdk_version") as response:
            running_version = tuple(map(int, (response.read().strip().split(b"."))))
    except Exception as e:
        logging.error(f"Error fetching current version: {e}")
        sys.exit(0)

    if running_version < min_version:
        logging.error(
            f"Currently running version too old! Minimum: {min_version}, Found: {running_version}"
        )
        sys.exit(1)


if __name__ == "__main__":
    check_sdk()
