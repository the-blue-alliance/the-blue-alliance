import json

import pytest

from google.appengine.ext import ndb

from backend.api.handlers.helpers.model_properties import (
    filter_event_properties,
    filter_match_properties,
    filter_team_properties,
    ModelType,
    simple_event_properties,
    simple_match_properties,
    simple_team_properties,
)
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.queries.dict_converters.event_converter import EventConverter
from backend.common.queries.dict_converters.match_converter import MatchConverter
from backend.common.queries.dict_converters.team_converter import TeamConverter


def test_filter_event_properties(ndb_stub) -> None:
    event = EventConverter(
        Event(
            id="2020casj",
            event_type_enum=EventType.REGIONAL,
            event_short="casj",
            year=2020,
        )
    ).convert(ApiMajorVersion.API_V3)

    assert set(event.keys()).difference(set(simple_event_properties)) != set()

    simple = filter_event_properties([event], ModelType("simple"))[0]
    assert set(simple.keys()).difference(set(simple_event_properties)) == set()

    key = filter_event_properties([event], ModelType("keys"))[0]
    assert key == "2020casj"

    search = filter_event_properties([event], ModelType("search"))[0]
    assert set(search.keys()).difference(set(simple_event_properties)) == set()

    assert filter_event_properties([], ModelType("bad_type")) == []
    with pytest.raises(Exception):
        filter_event_properties([event], ModelType("bad_type"))


def test_filter_match_properties(ndb_stub) -> None:
    match = MatchConverter(
        Match(
            id="2020casj_qm1",
            year=2020,
            event=ndb.Key("Event", "2020casj"),
            comp_level="qm",
            match_number=1,
            set_number=1,
            alliances_json=json.dumps(
                {
                    "red": {"score": 0, "teams": []},
                    "blue": {"score": 0, "teams": []},
                }
            ),
        )
    ).convert(ApiMajorVersion.API_V3)

    assert set(match.keys()).difference(set(simple_match_properties)) != set()

    simple = filter_match_properties([match], ModelType("simple"))[0]
    assert set(simple.keys()).difference(set(simple_match_properties)) == set()

    key = filter_match_properties([match], ModelType("keys"))[0]
    assert key == "2020casj_qm1"

    assert filter_match_properties([], ModelType("bad_type")) == []
    with pytest.raises(Exception):
        filter_match_properties([match], ModelType("bad_type"))


def test_filter_team_properties(ndb_stub) -> None:
    team = TeamConverter(Team(id="frc604")).convert(ApiMajorVersion.API_V3)

    assert set(team.keys()).difference(set(simple_team_properties)) != set()

    simple = filter_team_properties([team], ModelType("simple"))[0]
    assert set(simple.keys()).difference(set(simple_team_properties)) == set()

    key = filter_team_properties([team], ModelType("keys"))[0]
    assert key == "frc604"

    search = filter_team_properties([team], ModelType("search"))[0]
    assert set(search.keys()).difference(set(simple_team_properties)) == set()

    assert filter_team_properties([], ModelType("bad_type")) == []
    with pytest.raises(Exception):
        filter_team_properties([team], ModelType("bad_type"))
