import json
from datetime import datetime
from typing import Optional

import pytest
from freezegun import freeze_time
from google.cloud import ndb

from backend.common.consts import comp_level
from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.models.alliance import MatchAlliance
from backend.common.models.event import Event
from backend.common.models.match import Match


def get_base_elim_match(**kwargs) -> Match:
    return Match(
        id="2010ct_sf1m2",
        event=ndb.Key(Event, "2010ct"),
        year=2010,
        comp_level=CompLevel.SF,
        set_number=1,
        match_number=2,
        **kwargs
    )


def get_base_finals_match(**kwargs) -> Match:
    return Match(
        id="2010ct_f1m3",
        event=ndb.Key(Event, "2010ct"),
        year=2010,
        comp_level=CompLevel.F,
        set_number=1,
        match_number=3,
        **kwargs
    )


def get_base_qual_match(**kwargs) -> Match:
    return Match(
        id="2010ct_qm20",
        event=ndb.Key(Event, "2010ct"),
        year=2010,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=20,
        **kwargs
    )


@pytest.mark.parametrize("key", ["2019nyny_qm1", "2010ct_sf1m3"])
def test_valid_key_names(key: str) -> None:
    assert Match.validate_key_name(key) is True


@pytest.mark.parametrize("key", ["frc177", "2010ct_qm1m1", "2010ctf1m1", "2010ct_f1"])
def test_invalid_key_names(key: str) -> None:
    assert Match.validate_key_name(key) is False


def test_basic_fields() -> None:
    match = get_base_elim_match()
    assert match.key_name == "2010ct_sf1m2"
    assert match.comp_level == CompLevel.SF
    assert match.event_key_name == "2010ct"
    assert match.short_key == "sf1m2"
    assert match.play_order == 4002001
    assert match.name == "Semis"
    assert match.full_name == "Semifinals"


def test_lazy_load_alliances() -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(
            teams=["frc1", "frc2", "frc3"], score=-1, dqs=["frc1"], surrogates=[],
        ),
        AllianceColor.BLUE: MatchAlliance(
            teams=["frc4", "frc5", "frc6"], score=-1, dqs=[], surrogates=["frc5"]
        ),
    }
    match = get_base_qual_match(alliances_json=json.dumps(alliance_dict))
    assert match._alliances is None

    expected_dict = alliance_dict
    assert expected_dict == match.alliances


def test_lazy_load_alliances_fill_props() -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=-1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=-1),
    }
    match = get_base_qual_match(alliances_json=json.dumps(alliance_dict))
    assert match._alliances is None

    expected_dict = alliance_dict
    expected_dict[AllianceColor.RED]["surrogates"] = []
    expected_dict[AllianceColor.RED]["dqs"] = []
    expected_dict[AllianceColor.BLUE]["surrogates"] = []
    expected_dict[AllianceColor.BLUE]["dqs"] = []
    assert expected_dict == match.alliances


def test_correct_bad_alliance_scores() -> None:
    alliance_dict = {
        AllianceColor.RED: {"teams": ["frc1", "frc2", "frc3"], "score": None},
        AllianceColor.BLUE: {"teams": ["frc4", "frc5", "frc6"], "score": -1},
    }
    match = get_base_qual_match(alliances_json=json.dumps(alliance_dict),)
    assert match._alliances is None

    alliances = match.alliances
    assert alliances[AllianceColor.RED]["score"] == -1
    assert alliances[AllianceColor.BLUE]["score"] == -1


def test_all_teams_dqd_in_elims() -> None:
    alliance_dict = {
        AllianceColor.RED: {
            "teams": ["frc1", "frc2", "frc3"],
            "score": 10,
            "dqs": ["frc1"],
        },
        AllianceColor.BLUE: {"teams": ["frc4", "frc5", "frc6"], "score": 11},
    }
    match = get_base_elim_match(alliances_json=json.dumps(alliance_dict),)
    assert match._alliances is None

    alliances = match.alliances
    assert match.comp_level in comp_level.ELIM_LEVELS
    assert alliances[AllianceColor.RED]["dqs"] == alliances[AllianceColor.RED]["teams"]


def test_match_team_keys() -> None:
    team_key_names = ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"]
    match = get_base_qual_match(team_key_names=team_key_names)

    assert [k.id() for k in match.team_keys] == team_key_names


def test_has_not_been_played() -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=-1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=-1),
    }
    match = get_base_qual_match(alliances_json=json.dumps(alliance_dict))
    assert match.has_been_played is False


def test_not_been_played() -> None:
    alliance_dict = {
        AllianceColor.RED: MatchAlliance(teams=["frc1", "frc2", "frc3"], score=1),
        AllianceColor.BLUE: MatchAlliance(teams=["frc4", "frc5", "frc6"], score=2),
    }
    match = get_base_qual_match(alliances_json=json.dumps(alliance_dict))
    assert match.has_been_played is True


def test_short_name() -> None:
    qual_match = get_base_qual_match()
    assert qual_match.short_name == "Q20"

    elim_match = get_base_elim_match()
    assert elim_match.short_name == "SF1-2"

    finals_match = get_base_finals_match()
    assert finals_match.short_name == "F3"


def test_tba_video() -> None:
    no_video = get_base_qual_match()
    assert no_video.tba_video is None

    has_video = get_base_qual_match(tba_videos=["mp4", "jpg"])
    video = has_video.tba_video
    assert video is not None
    assert video.thumbnail_path is not None
    assert video.streamable_path is not None
    assert video.downloadable_path is not None


def test_videos() -> None:
    no_videos = get_base_qual_match()
    assert no_videos.videos == []

    has_videos = get_base_qual_match(tba_videos=["mp4"])
    videos = has_videos.videos
    assert len(videos) == 1
    assert videos[0]["type"] == "tba"


@pytest.mark.parametrize(
    "actual_time, predicted_time, error_str",
    [
        (
            datetime(2019, 3, 1, 6, 0, 5),
            datetime(2019, 3, 1, 6, 0, 0),
            "00:00:05 early",
        ),
        (
            datetime(2019, 3, 1, 6, 0, 5),
            datetime(2019, 3, 1, 6, 0, 10),
            "00:00:05 late",
        ),
        (datetime(2019, 3, 1, 6, 0, 5), datetime(2019, 3, 1, 6, 0, 5), "On Time"),
    ],
)
def test_prediction_error(
    actual_time: datetime, predicted_time: datetime, error_str: str
) -> None:
    match = get_base_qual_match(actual_time=actual_time, predicted_time=predicted_time)
    assert match.prediction_error_str == error_str


@pytest.mark.parametrize(
    "actual_time, scheduled_time, error_str",
    [
        (
            datetime(2019, 3, 1, 6, 0, 5),
            datetime(2019, 3, 1, 6, 0, 0),
            "00:00:05 behind",
        ),
        (
            datetime(2019, 3, 1, 6, 0, 5),
            datetime(2019, 3, 1, 6, 0, 10),
            "00:00:05 ahead",
        ),
        (datetime(2019, 3, 1, 6, 0, 5), datetime(2019, 3, 1, 6, 0, 5), "On Time"),
    ],
)
def test_schedule_error(
    actual_time: datetime, scheduled_time: datetime, error_str: str
) -> None:
    match = get_base_qual_match(actual_time=actual_time, time=scheduled_time)
    assert match.schedule_error_str == error_str


@pytest.mark.parametrize(
    "current_time, match_time, nsec, within",
    [
        (datetime(2020, 3, 1, 6, 0, 0), None, 10, None),
        (datetime(2020, 3, 1, 6, 0, 0), datetime(2020, 3, 1, 6, 0, 5), 10, True),
        (datetime(2020, 3, 1, 6, 0, 0), datetime(2020, 3, 1, 6, 0, 30), 10, False),
    ],
)
def test_within_seconds(
    current_time: datetime, match_time: Optional[datetime], nsec: int, within: bool
) -> None:
    with freeze_time(current_time):
        match = get_base_qual_match(actual_time=match_time)
        assert match.within_seconds(nsec) == within


@pytest.mark.parametrize(
    "red_score, blue_score, winner",
    [(10, 0, AllianceColor.RED), (0, 10, AllianceColor.BLUE), (10, 10, "")],
)
def test_winning_alliance_not_2015(
    red_score: int, blue_score: int, winner: AllianceColor,
) -> None:
    alliances = {
        AllianceColor.RED: MatchAlliance(
            teams=["frc1", "frc2", "frc3"], score=red_score,
        ),
        AllianceColor.BLUE: MatchAlliance(
            teams=["frc4", "frc5", "frc6"], score=blue_score,
        ),
    }
    match = Match(
        id=Match.renderKeyName("2010ct", CompLevel.QM, 1, 1),
        event=ndb.Key(Event, "2010ct"),
        year=2010,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json=json.dumps(alliances),
    )
    assert match.winning_alliance == winner


@pytest.mark.parametrize(
    "comp_level, red_score, blue_score, winner",
    [
        (CompLevel.QM, 10, 0, ""),
        (CompLevel.QF, 0, 10, ""),
        (CompLevel.SF, 10, 10, "",),
        (CompLevel.F, 15, 10, AllianceColor.RED,),
    ],
)
def test_winning_alliance_2015(
    comp_level: CompLevel, red_score: int, blue_score: int, winner: AllianceColor,
) -> None:
    alliances = {
        AllianceColor.RED: MatchAlliance(
            teams=["frc1", "frc2", "frc3"], score=red_score,
        ),
        AllianceColor.BLUE: MatchAlliance(
            teams=["frc4", "frc5", "frc6"], score=blue_score,
        ),
    }
    match = Match(
        id=Match.renderKeyName("2015ct", comp_level, 1, 1),
        event=ndb.Key(Event, "2015ct"),
        year=2015,
        comp_level=comp_level,
        set_number=1,
        match_number=1,
        alliances_json=json.dumps(alliances),
    )
    assert match.winning_alliance == winner


@pytest.mark.parametrize(
    "old_ts, seconds",
    [
        ("5m6s", "306"),
        ("1m02s", "62"),
        ("10s", "10"),
        ("2m", "120"),
        ("12345", "12345"),
        ("5h", "18000"),
        ("1h2m3s", "3723"),
    ],
)
def test_youtube_videos_formatted_timestamp_conversion(
    old_ts: str, seconds: str
) -> None:
    # Test timestamp conversion with both #t= and ?t=
    match = Match(youtube_videos=["TqY324xLU4s#t=" + old_ts])
    assert match.youtube_videos_formatted == ["TqY324xLU4s?start=" + seconds]

    match = Match(youtube_videos=["TqY324xLU4s?t=" + old_ts])
    assert match.youtube_videos_formatted == ["TqY324xLU4s?start=" + seconds]


def test_youtube_videos_formatted_no_timestamp() -> None:
    # Test that nothing is changed if there is no timestamp
    match = Match(youtube_videos=["TqY324xLU4s"])
    assert match.youtube_videos_formatted == ["TqY324xLU4s"]
