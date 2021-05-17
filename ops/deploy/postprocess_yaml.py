#! /usr/loca/bin/python3
import argparse
import os
import sys

import yaml


"""
There are some aspects of GAE YAML files that we don't want to have
committed to the repo and that we need to generate on the fly at deploy
time, based on secret environment variables

This script will parse the YAML file passed and add in those new fields.
The are:
 - set the REDIS_CACHE_URL environment variable
 - set up a vpc_access_connector to connect to Cloud Memorystore

This script depends on pyyaml
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("service", help="Path to yaml file for this service")

    args = parser.parse_args()

    with open(args.service) as service_file:
        service_config = yaml.safe_load(service_file)

    if "env_variables" not in service_config:
        service_config["env_variables"] = {}

    service_config["env_variables"]["REDIS_CACHE_URL"] = os.environ["REDIS_CACHE_URL"]

    service_config["vpc_access_connector"] = {
        "name": os.environ["VPC_CONNECTOR_NAME"],
    }

    with open(args.service, "w") as output_file:
        yaml.dump(service_config, output_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
