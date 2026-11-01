"""The golden events as TBA models, loaded from APIv3 JSON (``data/golden_events_api.json.gz``).

The events and matches are the ones of ``model/data/golden_stream.json.gz``. Events are
stored in the test datastore, because ``Match.winning_alliance`` reads the event of a tie.
"""

import copy
import gzip
import json
import os
from typing import Dict, List, Tuple

from google.appengine.ext import ndb

from backend.common.models.event import Event
from backend.common.models.keys import EventKey
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
