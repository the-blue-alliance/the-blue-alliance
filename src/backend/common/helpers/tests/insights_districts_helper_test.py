from google.appengine.ext import ndb

from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_districts_helper import InsightsDistrictsHelper
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team


def setup_district_with_team(year: int, abbreviation: str, team_key: str) -> None:
    District(
        id=f"{year}{abbreviation}",
        year=year,
        abbreviation=abbreviation,
        rankings=[
            {
                "team_key": team_key,
                "event_points": [{"total": 100, "district_cmp": False}],
            }
        ],
    ).put()
    Team(id=team_key, team_number=int(team_key.replace("frc", ""))).put()


def register_team_at_event(event_key: str, team_key: str, year: int) -> None:
    EventTeam(
        id=f"{event_key}_{team_key}",
        event=ndb.Key(Event, event_key),
        team=ndb.Key(Team, team_key),
        year=year,
    ).put()


def test_dcmp_appearances_counts_only_district_cmp_pre_division_era(ndb_stub) -> None:
    """Pre-2019: only DISTRICT_CMP events exist."""
    setup_district_with_team(2018, "ne", "frc5254")

    Event(
        id="2018nedcmp",
        year=2018,
        event_short="nedcmp",
        event_type_enum=EventType.DISTRICT_CMP,
    ).put()
    register_team_at_event("2018nedcmp", "frc5254", 2018)

    result = InsightsDistrictsHelper.make_insight_team_data("ne")
    assert result["frc5254"]["dcmp_appearances"] == 1


def test_dcmp_appearances_counts_division_event_when_team_eliminated_in_division(
    ndb_stub,
) -> None:
    """2019+: team attends a DISTRICT_CMP_DIVISION but is eliminated before the finals."""
    setup_district_with_team(2019, "ne", "frc5254")

    Event(
        id="2019nedcmp1",
        year=2019,
        event_short="nedcmp1",
        event_type_enum=EventType.DISTRICT_CMP_DIVISION,
    ).put()
    # Finals event exists but team 195 did not advance
    Event(
        id="2019nedcmp",
        year=2019,
        event_short="nedcmp",
        event_type_enum=EventType.DISTRICT_CMP,
    ).put()
    register_team_at_event("2019nedcmp1", "frc5254", 2019)

    result = InsightsDistrictsHelper.make_insight_team_data("ne")
    assert result["frc5254"]["dcmp_appearances"] == 1


def test_dcmp_appearances_no_double_count_when_advancing_to_finals(ndb_stub) -> None:
    """Team appears in both a DISTRICT_CMP_DIVISION and the DISTRICT_CMP finals in the same year."""
    setup_district_with_team(2019, "ne", "frc5254")

    Event(
        id="2019nedcmp1",
        year=2019,
        event_short="nedcmp1",
        event_type_enum=EventType.DISTRICT_CMP_DIVISION,
    ).put()
    Event(
        id="2019nedcmp",
        year=2019,
        event_short="nedcmp",
        event_type_enum=EventType.DISTRICT_CMP,
    ).put()
    register_team_at_event("2019nedcmp1", "frc5254", 2019)
    register_team_at_event("2019nedcmp", "frc5254", 2019)

    result = InsightsDistrictsHelper.make_insight_team_data("ne")
    assert result["frc5254"]["dcmp_appearances"] == 1


def test_dcmp_appearances_accumulates_across_years(ndb_stub) -> None:
    """Team attends DCMP across multiple years with mixed event types."""
    setup_district_with_team(2018, "ne", "frc5254")
    setup_district_with_team(2019, "ne", "frc5254")

    # 2018: pre-division era, team in DISTRICT_CMP finals only
    Event(
        id="2018nedcmp",
        year=2018,
        event_short="nedcmp",
        event_type_enum=EventType.DISTRICT_CMP,
    ).put()
    register_team_at_event("2018nedcmp", "frc5254", 2018)

    # 2019: team in DISTRICT_CMP_DIVISION only (eliminated in division)
    Event(
        id="2019nedcmp1",
        year=2019,
        event_short="nedcmp1",
        event_type_enum=EventType.DISTRICT_CMP_DIVISION,
    ).put()
    register_team_at_event("2019nedcmp1", "frc5254", 2019)

    result = InsightsDistrictsHelper.make_insight_team_data("ne")
    assert result["frc5254"]["dcmp_appearances"] == 2
