from datetime import datetime
from typing import List

from google.cloud import ndb
from requests_mock.mocker import Mocker as RequestsMocker

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team
from backend.common.queries.dict_converters.event_converter import EventConverter
from backend.common.queries.dict_converters.team_converter import TeamConverter
from backend.web.local.bootstrap import LocalDataBootstrap


def remove_auto_add_properties(model):
    model.created = None
    model.updated = None
    return model


def make_team(team_num: int) -> Team:
    return Team(
        id=f"frc{team_num}",
        team_number=team_num,
        nickname="Teh Chezy Pofs",
        name=f"Team {team_num}",
        website="https://www.thebluealliance.com",
    )


def make_event(event_key: str) -> Event:
    return Event(
        id=event_key,
        year=int(event_key[:4]),
        timezone_id="America/New_York",
        name=f"Regional: {event_key}",
        short_name="New York City",
        event_short=event_key[4:],
        event_type_enum=EventType.REGIONAL,
        playoff_type=PlayoffType.BRACKET_8_TEAM,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json="[]",
    )


def make_eventteam(event_key: str, team_key: str) -> EventTeam:
    return EventTeam(
        id=f"{event_key}_{team_key}",
        event=ndb.Key(Event, event_key),
        team=ndb.Key(Team, team_key),
        year=int(event_key[:4]),
    )


def mock_team_detail_url(m: RequestsMocker, team: Team) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/team/{team.key_name}",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        json=TeamConverter(team).convert(ApiMajorVersion.API_V3),
    )


def mock_event_detail_url(m: RequestsMocker, event: Event) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/event/{event.key_name}",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        json=EventConverter(event).convert(ApiMajorVersion.API_V3),
    )


def mock_event_teams_url(m: RequestsMocker, event_key: str, teams: List[Team]) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/event/{event_key}/teams",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        json=TeamConverter(teams).convert(ApiMajorVersion.API_V3),
    )


def test_bootstrap_unknown_key():
    resp = LocalDataBootstrap.bootstrap_key("asdf", "asdf")
    assert resp is None


def test_bootstrap_team(ndb_context, requests_mock: RequestsMocker) -> None:
    team = make_team(254)
    mock_team_detail_url(requests_mock, team)

    resp = LocalDataBootstrap.bootstrap_key("frc254", "test_apiv3")
    assert resp == "/team/254"

    stored_team = Team.get_by_id("frc254")
    assert team == remove_auto_add_properties(stored_team)


def test_bootstrap_event(ndb_context, requests_mock: RequestsMocker) -> None:
    event = make_event("2020nyny")
    team1 = make_team(254)
    team2 = make_team(255)
    mock_event_detail_url(requests_mock, event)
    mock_event_teams_url(requests_mock, event.key_name, [team1, team2])

    resp = LocalDataBootstrap.bootstrap_key("2020nyny", "test_apiv3")
    assert resp == "/event/2020nyny"

    stored_event = Event.get_by_id("2020nyny")
    assert event == remove_auto_add_properties(stored_event)

    stored_team1 = Team.get_by_id("frc254")
    assert team1 == remove_auto_add_properties(stored_team1)

    stored_team2 = Team.get_by_id("frc255")
    assert team2 == remove_auto_add_properties(stored_team2)

    stored_eventteam1 = EventTeam.get_by_id("2020nyny_frc254")
    assert make_eventteam("2020nyny", "frc254") == remove_auto_add_properties(
        stored_eventteam1
    )
    stored_eventteam2 = EventTeam.get_by_id("2020nyny_frc255")
    assert make_eventteam("2020nyny", "frc255") == remove_auto_add_properties(
        stored_eventteam2
    )
