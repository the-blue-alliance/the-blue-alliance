import argparse

from shell.lib import connect_to_ndb

from backend.common.models.event import Event

parser = argparse.ArgumentParser()
parser.add_argument("event_key")
args = parser.parse_args()

with connect_to_ndb():
    print(f"Fetching {args.event_key}...")
    print(Event.get_by_id(args.event_key))
