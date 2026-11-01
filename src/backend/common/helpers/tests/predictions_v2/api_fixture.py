"""The golden events as TBA models, loaded from APIv3 JSON (``data/golden_events_api.json.gz``).

The events and matches are the ones of ``model/data/golden_stream.json.gz``. Events are
stored in the test datastore, because ``Match.winning_alliance`` reads the event of a tie.
"""

import copy
import gzip
import json
import os
from typing import Dict, List, Set, Tuple

from google.appengine.ext import ndb

from backend.common.models.event import Event
from backend.common.models.keys import EventKey, Year
from backend.common.models.match import Match
from backend.common.queries.dict_converters.event_converter import EventConverter
from backend.common.queries.dict_converters.match_converter import MatchConverter

API_FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "data", "golden_events_api.json.gz"
)


def load_api_fixture() -> Tuple[Dict[EventKey, Event], List[Match]]:
    with gzip.open(API_FIXTURE_PATH, "rt") as f:
        data = json.load(f)
    events = {
        e["key"]: EventConverter.dictToModel_v3(copy.deepcopy(e))
        for e in data["events"]
    }
    ndb.put_multi(list(events.values()))
    matches = [
        MatchConverter.dictToModel_v3(copy.deepcopy(m))
        for event_matches in data["matches"].values()
        for m in event_matches
    ]
    return events, matches


def store_api_fixture(years: Set[Year]) -> Tuple[Dict[EventKey, Event], List[Match]]:
    """Store the fixture's events and matches of ``years`` in the test datastore."""
    events, matches = load_api_fixture()
    events = {k: e for k, e in events.items() if e.year in years}
    matches = [m for m in matches if m.event_key_name in events]
    ndb.put_multi(matches)
    return events, matches
