import datetime
import json
import time

from google.appengine.ext import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.comp_level import CompLevel
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.queries.dict_converters.match_converter import MatchConverter


def _match() -> Match:
    return Match(
        id="2019nyny_qm1",
        event=ndb.Key(Event, "2019nyny"),
        year=2019,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json=json.dumps(
            {
                "red": {
                    "teams": ["frc1", "frc2", "frc3"],
                    "score": 10,
                    "surrogates": ["frc3"],
                    "dqs": ["frc2"],
                },
                "blue": {
                    "teams": ["frc4", "frc5", "frc6"],
                    "score": 20,
                    "surrogates": [],
                },
            }
        ),
    )


def test_matchConverter_v3_no_times(ndb_context) -> None:
    converted = MatchConverter.matchConverter_v3(_match())
    assert converted == {
        "key": "2019nyny_qm1",
        "event_key": "2019nyny",
        "comp_level": CompLevel.QM,
        "set_number": 1,
        "match_number": 1,
        "alliances": {
            "red": {
                "team_keys": ["frc1", "frc2", "frc3"],
                "score": 10,
                "surrogate_team_keys": ["frc3"],
                "dq_team_keys": ["frc2"],
            },
            "blue": {
                "team_keys": ["frc4", "frc5", "frc6"],
                "score": 20,
                "surrogate_team_keys": [],
                "dq_team_keys": [],
            },
        },
        "winning_alliance": "blue",
        "score_breakdown": None,
        "videos": [],
        "time": None,
        "actual_time": None,
        "predicted_time": None,
        "post_result_time": None,
    }


def test_matchConverter_v3_times(ndb_context) -> None:
    match = _match()
    match.time = datetime.datetime(2019, 4, 6, 9, 0, 0)
    match.actual_time = datetime.datetime(2019, 4, 6, 9, 5, 0)
    match.predicted_time = datetime.datetime(2019, 4, 6, 9, 3, 0)
    match.post_result_time = datetime.datetime(2019, 4, 6, 9, 10, 0)

    converted = MatchConverter.matchConverter_v3(match)

    def as_timestamp(dt: datetime.datetime) -> int:
        return int(time.mktime(dt.timetuple()))

    assert converted["time"] == as_timestamp(datetime.datetime(2019, 4, 6, 9, 0, 0))
    assert converted["actual_time"] == as_timestamp(
        datetime.datetime(2019, 4, 6, 9, 5, 0)
    )
    assert converted["predicted_time"] == as_timestamp(
        datetime.datetime(2019, 4, 6, 9, 3, 0)
    )
    assert converted["post_result_time"] == as_timestamp(
        datetime.datetime(2019, 4, 6, 9, 10, 0)
    )


def test_convert(ndb_context) -> None:
    converted = MatchConverter([_match()]).convert(ApiMajorVersion.API_V3)
    assert converted == [MatchConverter.matchConverter_v3(_match())]


def test_dictToModel_v3_round_trip(ndb_context) -> None:
    match = _match()
    match.time = datetime.datetime(2019, 4, 1, 12, 0, 0)
    match.actual_time = datetime.datetime(2019, 4, 1, 12, 5, 0)
    match.predicted_time = datetime.datetime(2019, 4, 1, 12, 3, 0)
    match.post_result_time = datetime.datetime(2019, 4, 1, 12, 10, 0)
    match.score_breakdown_json = json.dumps(
        {"red": {"totalPoints": 10}, "blue": {"totalPoints": 20}}
    )
    match.youtube_videos = ["abc123"]
    match.tba_videos = [".mp4"]

    data = MatchConverter.matchConverter_v3(match)
    model = MatchConverter.dictToModel_v3(data)

    assert model.key.id() == "2019nyny_qm1"
    assert model.event == ndb.Key(Event, "2019nyny")
    assert model.year == 2019
    assert model.comp_level == CompLevel.QM
    assert model.set_number == 1
    assert model.match_number == 1
    assert model.time == match.time
    assert model.actual_time == match.actual_time
    assert model.predicted_time == match.predicted_time
    assert model.post_result_time == match.post_result_time
    assert model.score_breakdown == match.score_breakdown
    assert model.team_key_names == ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"]
    assert model.alliances[AllianceColor.RED]["dqs"] == ["frc2"]
    assert model.alliances[AllianceColor.BLUE]["dqs"] == []
    assert model.alliances[AllianceColor.RED]["surrogates"] == ["frc3"]
    assert model.alliances[AllianceColor.BLUE]["score"] == 20
    # Only YouTube videos survive the round trip.
    assert model.youtube_videos == ["abc123"]


def test_dictToModel_v3_no_times(ndb_context) -> None:
    data = MatchConverter.matchConverter_v3(_match())
    model = MatchConverter.dictToModel_v3(data)

    assert model.time is None
    assert model.actual_time is None
    assert model.predicted_time is None
    assert model.post_result_time is None
    assert model.score_breakdown_json is None
    assert model.youtube_videos == []
