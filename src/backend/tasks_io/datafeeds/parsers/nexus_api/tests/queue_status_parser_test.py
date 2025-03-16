import datetime
import json
from typing import Optional

import pytest
from google.appengine.ext import ndb
from pyre_extensions import JSON

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.models.event import Event
from backend.common.models.event_queue_status import (
    EventQueueStatus,
    NexusCurrentlyQueueing,
    NexusMatch,
    NexusMatchStatus,
    NexusMatchTiming,
)
from backend.common.models.keys import MatchKey
from backend.common.models.match import Match
from backend.tasks_io.datafeeds.parsers.nexus_api.queue_status_parser import (
    NexusAPIQueueStatusParser,
)


def create_event(playoff_type: PlayoffType = PlayoffType.DOUBLE_ELIM_8_TEAM) -> Event:
    e = Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        start_date=datetime.datetime(2019, 4, 1),
        end_date=datetime.datetime(2019, 4, 3),
        event_type_enum=EventType.REGIONAL,
        playoff_type=playoff_type,
        official=True,
    )
    e.put()
    return e


def create_match(played: bool) -> Match:
    m = Match(
        id="2019casj_qm1",
        event=ndb.Key(Event, "2019casj"),
        comp_level=CompLevel.QM,
        match_number=1,
        set_number=1,
        year=2019,
        alliances_json=json.dumps(
            {
                "red": {"score": 10 if played else -1, "teams": []},
                "blue": {"score": 10 if played else -1, "teams": []},
            }
        ),
    )
    m.put()
    return m


def test_wrong_playoff_type(ndb_stub) -> None:
    e = create_event(playoff_type=PlayoffType.BRACKET_8_TEAM)
    data: JSON = []
    parsed = NexusAPIQueueStatusParser(e).parse(data)
    assert parsed is None


def test_bad_format(ndb_stub) -> None:
    e = create_event()
    data: JSON = []
    parsed = NexusAPIQueueStatusParser(e).parse(data)
    assert parsed is None


def test_missing_matches(ndb_stub) -> None:
    e = create_event()
    data: JSON = {"matches": {}}
    parsed = NexusAPIQueueStatusParser(e).parse(data)
    assert parsed is None


def test_parse_bad_match_key(ndb_stub) -> None:
    e = create_event()
    data: JSON = {
        "dataAsOfTime": 0,
        "nowQueueing": "Practice 1",
        "matches": [
            {
                "label": "asdf",
            }
        ],
    }
    parsed = NexusAPIQueueStatusParser(e).parse(data)
    assert parsed == EventQueueStatus(
        data_as_of_ms=0,
        now_queueing=None,
        matches={},
    )


def test_parse_bad_missing_match(ndb_stub) -> None:
    e = create_event()
    data: JSON = {
        "dataAsOfTime": 0,
        "nowQueueing": "Qualification 1",
        "matches": [
            {
                "label": "2019casj_qm1",
            }
        ],
    }
    parsed = NexusAPIQueueStatusParser(e).parse(data)
    assert parsed == EventQueueStatus(
        data_as_of_ms=0,
        now_queueing=None,
        matches={},
    )


def test_parse_match_upcoming(ndb_stub) -> None:
    e = create_event()
    create_match(played=False)
    data: JSON = {
        "dataAsOfTime": 0,
        "nowQueuing": "Qualification 1",
        "matches": [
            {
                "label": "Qualification 1",
                "status": "Now queuing",
                "times": {
                    "estimatedQueueTime": 0,
                    "estimatedStartTime": 0,
                },
            }
        ],
    }
    parsed = NexusAPIQueueStatusParser(e).parse(data)
    assert parsed == EventQueueStatus(
        data_as_of_ms=0,
        now_queueing=NexusCurrentlyQueueing(
            match_key="2019casj_qm1",
            match_name="Qualification 1",
        ),
        matches={
            "2019casj_qm1": NexusMatch(
                label="Qualification 1",
                status=NexusMatchStatus.NOW_QUEUING,
                played=False,
                times=NexusMatchTiming(
                    estimated_queue_time_ms=0,
                    estimated_start_time_ms=0,
                ),
            )
        },
    )


def test_parse_match_nothing_queing(ndb_stub) -> None:
    e = create_event()
    create_match(played=False)
    data: JSON = {
        "dataAsOfTime": 0,
        "matches": [
            {
                "label": "Qualification 1",
                "status": "Now queuing",
                "times": {
                    "estimatedQueueTime": 0,
                    "estimatedStartTime": 0,
                },
            }
        ],
    }
    parsed = NexusAPIQueueStatusParser(e).parse(data)
    assert parsed == EventQueueStatus(
        data_as_of_ms=0,
        now_queueing=None,
        matches={
            "2019casj_qm1": NexusMatch(
                label="Qualification 1",
                status=NexusMatchStatus.NOW_QUEUING,
                played=False,
                times=NexusMatchTiming(
                    estimated_queue_time_ms=0,
                    estimated_start_time_ms=0,
                ),
            )
        },
    )


def test_parse_match_nothing_played(ndb_stub) -> None:
    e = create_event()
    create_match(played=True)
    data: JSON = {
        "dataAsOfTime": 0,
        "matches": [
            {
                "label": "Qualification 1",
                "status": "Now queuing",
                "times": {
                    "estimatedQueueTime": 0,
                    "estimatedStartTime": 0,
                },
            }
        ],
    }
    parsed = NexusAPIQueueStatusParser(e).parse(data)
    assert parsed == EventQueueStatus(
        data_as_of_ms=0,
        now_queueing=None,
        matches={
            "2019casj_qm1": NexusMatch(
                label="Qualification 1",
                status=NexusMatchStatus.NOW_QUEUING,
                played=True,
                times=NexusMatchTiming(
                    estimated_queue_time_ms=0,
                    estimated_start_time_ms=0,
                ),
            )
        },
    )


@pytest.mark.parametrize(
    "match_label,match_key",
    [
        ("asdf", None),
        ("Practice 1", None),
        ("Qualification 1", "2019casj_qm1"),
        ("Qualification 10", "2019casj_qm10"),
        ("Qualification 10 Replay", "2019casj_qm10"),
        ("Playoff 1", "2019casj_sf1m1"),
        ("Playoff 8", "2019casj_sf8m1"),
        ("Final 1", "2019casj_f1m1"),
        ("Final 2", "2019casj_f1m2"),
    ],
)
def test_parse_match_label(
    ndb_stub, match_label: str, match_key: Optional[MatchKey]
) -> None:
    e = create_event()
    parsed_key = NexusAPIQueueStatusParser(e)._parse_match_description(match_label)
    assert parsed_key == match_key


@pytest.mark.parametrize(
    "api_status,status",
    [
        ("asfd", None),
        ("Queuing soon", NexusMatchStatus.QUEUING_SOON),
        ("Now queuing", NexusMatchStatus.NOW_QUEUING),
        ("On deck", NexusMatchStatus.ON_DECK),
        ("On field", NexusMatchStatus.ON_FIELD),
    ],
)
def test_nexus_match_status_parsing(
    api_status: str, status: Optional[NexusMatchStatus]
) -> None:
    if status is None:
        with pytest.raises(ValueError):
            NexusMatchStatus.from_string(api_status)
    else:
        parsed_status = NexusMatchStatus.from_string(api_status)
        assert parsed_status == status
        assert parsed_status.to_string() == api_status
