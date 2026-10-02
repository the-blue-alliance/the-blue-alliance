import json
from typing import List, Optional

from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_districts_helper import (
    get_state_or_country_if_international,
    InsightsDistrictsHelper,
    state_short_code_to_full_name,
)
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
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


def put_district_event(
    event_key: str,
    event_type: EventType,
    district_key: Optional[str],
    team_keys: List[str],
    country: str = "USA",
    state_prov: str = "NY",
) -> None:
    year = int(event_key[:4])
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
        district_key=ndb.Key(District, district_key) if district_key else None,
        country=country,
        state_prov=state_prov,
    ).put()
    for team_key in team_keys:
        register_team_at_event(event_key, team_key, year)


def put_award(
    event_key: str,
    award_type: AwardType,
    event_type: EventType,
    team_keys: List[str],
) -> None:
    Award(
        id=f"{event_key}_{award_type}",
        year=int(event_key[:4]),
        award_type_enum=award_type,
        event_type_enum=event_type,
        event=ndb.Key(Event, event_key),
        name_str=str(award_type),
        team_list=[ndb.Key(Team, team_key) for team_key in team_keys],
    ).put()


def put_match(
    event_key: str,
    comp_level: CompLevel,
    match_number: int,
    red_score: int,
    blue_score: int,
    red_teams: List[str],
    blue_teams: List[str],
) -> None:
    Match(
        id=f"{event_key}_{comp_level}1m{match_number}",
        event=ndb.Key(Event, event_key),
        year=int(event_key[:4]),
        comp_level=comp_level,
        set_number=1,
        match_number=match_number,
        team_key_names=red_teams + blue_teams,
        alliances_json=json.dumps(
            {
                "red": {"teams": red_teams, "score": red_score},
                "blue": {"teams": blue_teams, "score": blue_score},
            }
        ),
    ).put()


def test_make_insight_team_data_aggregates_points_awards_and_matches(
    ndb_stub,
) -> None:
    for team_number in range(1, 7):
        Team(id=f"frc{team_number}", team_number=team_number).put()

    District(
        id="2018ne",
        year=2018,
        abbreviation="ne",
        rankings=[
            {
                "team_key": "frc1",
                "event_points": [
                    {"total": 40, "district_cmp": False},
                    {"total": 60, "district_cmp": True},
                ],
            },
            # Some totals arrive as floats
            {
                "team_key": "frc2",
                "event_points": [{"total": 50.0, "district_cmp": False}],
            },
            # Teams that never earned points in the district are dropped
            {"team_key": "frc3", "event_points": []},
        ],
    ).put()
    District(
        id="2015ne",
        year=2015,
        abbreviation="ne",
        rankings=[
            {"team_key": "frc1", "event_points": [{"total": 10, "district_cmp": False}]}
        ],
    ).put()
    # 2021 (the at-home season) is skipped entirely
    District(
        id="2021ne",
        year=2021,
        abbreviation="ne",
        rankings=[
            {
                "team_key": "frc1",
                "event_points": [{"total": 999, "district_cmp": False}],
            }
        ],
    ).put()

    red = ["frc1", "frc2", "frc3"]
    blue = ["frc4", "frc5", "frc6"]
    put_district_event("2018nea", EventType.DISTRICT, "2018ne", red + blue)
    put_district_event("2018neb", EventType.DISTRICT, "2018ne", red)
    put_district_event("2018nec", EventType.DISTRICT, "2018ne", ["frc1"])
    put_district_event("2018necmp", EventType.DISTRICT_CMP, "2018ne", ["frc1", "frc2"])
    put_district_event("2015nea", EventType.DISTRICT, "2015ne", ["frc1"])
    put_district_event("2018arc", EventType.CMP_DIVISION, None, ["frc1"])

    put_award("2018nea", AwardType.WINNER, EventType.DISTRICT, red)
    put_award("2018nea", AwardType.WOODIE_FLOWERS, EventType.DISTRICT, ["frc1"])
    put_award("2018nea", AwardType.DEANS_LIST, EventType.DISTRICT, ["frc2"])
    put_award("2018nea", AwardType.VOLUNTEER, EventType.DISTRICT, ["frc6"])
    put_award(
        "2018nea", AwardType.ENGINEERING_INSPIRATION, EventType.DISTRICT, ["frc2"]
    )
    put_award("2018necmp", AwardType.WINNER, EventType.DISTRICT_CMP, ["frc1", "frc2"])
    put_award("2018necmp", AwardType.CHAIRMANS, EventType.DISTRICT_CMP, ["frc3"])

    put_match("2018nea", CompLevel.QM, 1, 50, 30, red, blue)
    put_match("2018nea", CompLevel.QM, 2, 20, 60, red, blue)
    put_match("2018nea", CompLevel.QM, 3, -1, -1, red, blue)  # unplayed
    put_match("2018nea", CompLevel.QM, 4, 40, 40, red, blue)  # tie
    put_match("2018nea", CompLevel.SF, 1, 70, 10, red, blue)
    put_match("2018nea", CompLevel.F, 1, 55, 60, red, blue)
    # 2015 ties are not recorded as ties
    put_match("2015nea", CompLevel.QM, 1, 10, 10, ["frc1"], ["frc4"])

    result = InsightsDistrictsHelper.make_insight_team_data("ne")

    assert set(result.keys()) == {"frc1", "frc2"}
    assert result["frc1"] == {
        "district_seasons": 2,
        "total_district_points": 110,
        "total_pre_dcmp_district_points": 50,
        "district_event_wins": 1,
        "dcmp_wins": 1,
        "team_awards": 2,
        "individual_awards": 1,
        "quals_record": {"wins": 1, "losses": 1, "ties": 1},
        "elims_record": {"wins": 1, "losses": 1, "ties": 0},
        "blue_banners": 3,
        "in_district_extra_play_count": 1,
        "total_matches_played": 6,
        "dcmp_appearances": 1,
        "cmp_appearances": 1,
    }
    assert result["frc2"] == {
        "district_seasons": 1,
        "total_district_points": 50,
        "total_pre_dcmp_district_points": 50,
        "district_event_wins": 1,
        "dcmp_wins": 1,
        "team_awards": 3,
        "individual_awards": 1,
        "quals_record": {"wins": 1, "losses": 1, "ties": 1},
        "elims_record": {"wins": 1, "losses": 1, "ties": 0},
        "blue_banners": 2,
        "in_district_extra_play_count": 0,
        "total_matches_played": 5,
        "dcmp_appearances": 1,
        "cmp_appearances": 0,
    }


def test_make_insight_team_data_for_unknown_district_is_empty(ndb_stub) -> None:
    assert InsightsDistrictsHelper.make_insight_team_data("ne") == {}


def test_make_team_deltas() -> None:
    yearly_teams = {2019: {"frc1", "frc2"}, 2020: {"frc2", "frc3"}}

    gained, lost = InsightsDistrictsHelper._make_team_deltas(yearly_teams, 2019, 2020)
    assert gained == ["frc3"]
    assert lost == ["frc1"]

    # Missing years are treated as having no teams
    gained, lost = InsightsDistrictsHelper._make_team_deltas(yearly_teams, 2018, 2019)
    assert sorted(gained) == ["frc1", "frc2"]
    assert lost == []


def put_district_team(
    district_key: str, team_key: str, country: str, state_prov: str
) -> None:
    year = int(district_key[:4])
    Team(
        id=team_key,
        team_number=int(team_key.replace("frc", "")),
        country=country,
        state_prov=state_prov,
    ).put()
    DistrictTeam(
        id=f"{district_key}_{team_key}",
        team=ndb.Key(Team, team_key),
        year=year,
        district_key=ndb.Key(District, district_key),
    ).put()


def test_make_insight_district_data_tracks_growth_by_region(ndb_stub) -> None:
    District(id="2019ne", year=2019, abbreviation="ne").put()
    District(id="2020ne", year=2020, abbreviation="ne").put()

    put_district_team("2019ne", "frc1", "USA", "NY")
    put_district_team("2019ne", "frc2", "USA", "MA")
    put_district_team("2019ne", "frc3", "Canada", "ON")
    put_district_team("2020ne", "frc1", "USA", "NY")
    put_district_team("2020ne", "frc3", "Canada", "ON")
    put_district_team("2020ne", "frc4", "Israel", "TA")
    # A known one-off team/year exception is excluded from growth stats
    put_district_team("2020ne", "frc8393", "USA", "PA")

    put_district_event("2019nea", EventType.DISTRICT, "2019ne", [], "USA", "NY")
    put_district_event("2019neb", EventType.DISTRICT, "2019ne", [], "Canada", "ON")
    # Regions with events but no teams do not get their own entry
    put_district_event("2019nec", EventType.DISTRICT, "2019ne", [], "USA", "CT")
    put_district_event("2020nea", EventType.DISTRICT, "2020ne", [], "USA", "NY")

    result = InsightsDistrictsHelper.make_insight_district_data("ne")

    district_wide = result["district_wide_data"]
    assert district_wide["yearly_active_team_count"] == {2019: 3, 2020: 3}
    assert district_wide["yearly_event_count"] == {2019: 3, 2020: 1}
    assert {
        year: sorted(teams)
        for year, teams in district_wide["yearly_gained_teams"].items()
    } == {2019: ["frc1", "frc2", "frc3"], 2020: ["frc4"]}
    assert district_wide["yearly_lost_teams"] == {2019: [], 2020: ["frc2"]}

    assert set(result["region_data"].keys()) == {
        "New York",
        "Massachusetts",
        "ON",
        "Israel",
    }
    assert result["region_data"]["New York"] == {
        "yearly_active_team_count": {2019: 1, 2020: 1},
        "yearly_event_count": {2019: 1, 2020: 1},
        "yearly_gained_teams": {2019: ["frc1"], 2020: []},
        "yearly_lost_teams": {2019: [], 2020: []},
    }
    assert result["region_data"]["Massachusetts"] == {
        "yearly_active_team_count": {2019: 1},
        "yearly_event_count": {},
        "yearly_gained_teams": {2019: ["frc2"]},
        "yearly_lost_teams": {2019: []},
    }
    assert result["region_data"]["ON"] == {
        "yearly_active_team_count": {2019: 1, 2020: 1},
        "yearly_event_count": {2019: 1},
        "yearly_gained_teams": {2019: ["frc3"], 2020: []},
        "yearly_lost_teams": {2019: [], 2020: []},
    }
    assert result["region_data"]["Israel"] == {
        "yearly_active_team_count": {2020: 1},
        "yearly_event_count": {},
        "yearly_gained_teams": {2020: ["frc4"]},
        "yearly_lost_teams": {2020: []},
    }


def test_make_insight_district_data_for_unknown_district_is_empty(ndb_stub) -> None:
    assert InsightsDistrictsHelper.make_insight_district_data("ne") == {
        "region_data": {},
        "district_wide_data": {
            "yearly_active_team_count": {},
            "yearly_event_count": {},
            "yearly_gained_teams": {},
            "yearly_lost_teams": {},
        },
    }


def test_get_state_or_country_if_international() -> None:
    assert (
        get_state_or_country_if_international(Team(country="USA", state_prov="NY"))
        == "New York"
    )
    # Canadian provinces are not in the US state map, so the code is kept
    assert (
        get_state_or_country_if_international(Event(country="Canada", state_prov="ON"))
        == "ON"
    )
    assert (
        get_state_or_country_if_international(Team(country="Israel", state_prov="TA"))
        == "Israel"
    )


def test_state_short_code_to_full_name() -> None:
    assert state_short_code_to_full_name("NY") == "New York"
    assert state_short_code_to_full_name("ZZ") == "ZZ"
