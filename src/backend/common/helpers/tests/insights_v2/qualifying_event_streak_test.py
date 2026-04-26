from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.compute import compute_insights_for_year
from backend.common.helpers.insights_v2.qualifying_event_streak import (
    LongestQualifyingEventStreakV2Calculator,
)
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team

_ALLIANCES_JSON = (
    '{"red": {"score": 0, "teams": ["frc1", "frc2", "frc3"]},'
    ' "blue": {"score": 0, "teams": ["frc4", "frc5", "frc6"]}}'
)


def _put_event(event_key: str, year: int, event_type: EventType) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
    ).put()


def _put_winner_award(event_key: str, year: int, team_keys: list) -> None:
    Award(
        id=f"{event_key}_1",
        year=year,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, event_key),
        name_str="Regional Winners",
        team_list=[ndb.Key(Team, k) for k in team_keys],
    ).put()


def _put_match(event_key: str, year: int, team_keys: list) -> None:
    Match(
        id=f"{event_key}_qm1",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, event_key),
        year=year,
        match_number=1,
        set_number=1,
        team_key_names=team_keys,
        alliances_json=_ALLIANCES_JSON,
    ).put()


def test_consecutive_wins_build_streak(ndb_stub) -> None:
    _put_event("2022nyny", 2022, EventType.REGIONAL)
    _put_winner_award("2022nyny", 2022, ["frc254"])
    _put_match("2022nyny", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    _put_event("2023nyny", 2023, EventType.REGIONAL)
    _put_winner_award("2023nyny", 2023, ["frc254"])
    _put_match("2023nyny", 2023, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(
        0, [LongestQualifyingEventStreakV2Calculator()]
    )

    assert len(insights) == 1
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc254"
    assert top["key_type"] == "team"
    assert top["streak_length"] == 2
    assert top["start"] == "2022nyny"
    assert top["end"] == "2023nyny"
    assert top["is_active"] is True


def test_streak_broken_records_best(ndb_stub) -> None:
    _put_event("2022nyny", 2022, EventType.REGIONAL)
    _put_winner_award("2022nyny", 2022, ["frc254"])
    _put_match("2022nyny", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    # frc254 participates but doesn't win — streak resets to 0, longest remains 1
    _put_event("2023nyny", 2023, EventType.REGIONAL)
    _put_match("2023nyny", 2023, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(
        0, [LongestQualifyingEventStreakV2Calculator()]
    )

    assert len(insights) == 1
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc254"
    assert top["streak_length"] == 1
    assert top["start"] == "2022nyny"
    assert top["end"] == "2022nyny"
    assert top["is_active"] is False


def test_non_qualifying_event_types_ignored(ndb_stub) -> None:
    # A district championship should not count toward the streak
    _put_event("2022necmp", 2022, EventType.DISTRICT_CMP)
    Award(
        id="2022necmp_1",
        year=2022,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.DISTRICT_CMP,
        event=ndb.Key(Event, "2022necmp"),
        name_str="District Championship Winners",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()
    Match(
        id="2022necmp_qm1",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, "2022necmp"),
        year=2022,
        match_number=1,
        set_number=1,
        team_key_names=["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"],
        alliances_json=_ALLIANCES_JSON,
    ).put()

    insights = compute_insights_for_year(
        0, [LongestQualifyingEventStreakV2Calculator()]
    )
    assert insights == []


def test_cancelled_event_does_not_break_streak(ndb_stub) -> None:
    _put_event("2019nyny", 2019, EventType.REGIONAL)
    _put_winner_award("2019nyny", 2019, ["frc254"])
    _put_match("2019nyny", 2019, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    # Cancelled event with no matches — should not break frc254's active streak
    _put_event("2020nyny", 2020, EventType.REGIONAL)

    _put_event("2022nyny", 2022, EventType.REGIONAL)
    _put_winner_award("2022nyny", 2022, ["frc254"])
    _put_match("2022nyny", 2022, ["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"])

    insights = compute_insights_for_year(
        0, [LongestQualifyingEventStreakV2Calculator()]
    )

    assert len(insights) == 1
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc254"
    assert top["streak_length"] == 2
    assert top["start"] == "2019nyny"
    assert top["end"] == "2022nyny"
    assert top["is_active"] is True


def test_district_events_count_toward_streak(ndb_stub) -> None:
    _put_event("2022mabos", 2022, EventType.DISTRICT)
    Award(
        id="2022mabos_1",
        year=2022,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.DISTRICT,
        event=ndb.Key(Event, "2022mabos"),
        name_str="District Winners",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()
    Match(
        id="2022mabos_qm1",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, "2022mabos"),
        year=2022,
        match_number=1,
        set_number=1,
        team_key_names=["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"],
        alliances_json=_ALLIANCES_JSON,
    ).put()

    _put_event("2023manew", 2023, EventType.DISTRICT)
    Award(
        id="2023manew_1",
        year=2023,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.DISTRICT,
        event=ndb.Key(Event, "2023manew"),
        name_str="District Winners",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()
    Match(
        id="2023manew_qm1",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, "2023manew"),
        year=2023,
        match_number=1,
        set_number=1,
        team_key_names=["frc254", "frc1", "frc2", "frc3", "frc4", "frc5"],
        alliances_json=_ALLIANCES_JSON,
    ).put()

    insights = compute_insights_for_year(
        0, [LongestQualifyingEventStreakV2Calculator()]
    )

    assert len(insights) == 1
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc254"
    assert top["streak_length"] == 2


def test_real_data_frc1796_streak(ndb_stub, test_data_importer) -> None:
    # frc1796 wins both 2019nyny (REGIONAL) and 2024nytr (REGIONAL);
    # with only these two events loaded, their streak should be 2
    test_data_importer.import_event(__file__, "../data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "../data/2019nyny_awards.json")
    test_data_importer.import_match_list(__file__, "../data/2019nyny_matches.json")
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")
    test_data_importer.import_match_list(__file__, "../data/2024nytr_matches.json")

    insights = compute_insights_for_year(
        0, [LongestQualifyingEventStreakV2Calculator()]
    )

    assert len(insights) == 1
    assert insights[0].category == "streak"
    top = insights[0].data["entries"][0]
    assert top["key"] == "frc1796"
    assert top["streak_length"] == 2
    assert top["start"] == "2019nyny"
    assert top["end"] == "2024nytr"
    assert top["is_active"] is True
