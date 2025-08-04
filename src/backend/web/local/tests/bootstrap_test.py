import json
from datetime import datetime
from typing import cast, Dict, List

from google.appengine.ext import ndb
from requests_mock.mocker import Mocker as RequestsMocker

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import MediaType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.helpers.deferred import run_from_task
from backend.common.models.alliance import EventAlliance, MatchAlliance
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_predictions import EventPredictions
from backend.common.models.event_ranking import EventRanking
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, MatchKey, TeamKey, TeamNumber, Year
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.dict_converters.award_converter import AwardConverter
from backend.common.queries.dict_converters.event_converter import EventConverter
from backend.common.queries.dict_converters.event_details_converter import (
    EventDetailsConverter,
)
from backend.common.queries.dict_converters.match_converter import MatchConverter
from backend.common.queries.dict_converters.media_converter import MediaConverter
from backend.common.queries.dict_converters.team_converter import TeamConverter
from backend.web.local.bootstrap import LocalDataBootstrap


def remove_auto_add_properties(model):
    if hasattr(model, "created"):
        delattr(model, "created")
    if hasattr(model, "updated"):
        delattr(model, "updated")
    if hasattr(model, "no_auto_update"):
        delattr(model, "no_auto_update")
    return model


def make_team(team_num: TeamNumber) -> Team:
    return Team(
        id=f"frc{team_num}",
        team_number=team_num,
        nickname="Teh Chezy Pofs",
        name=f"Team {team_num}",
        website="https://www.thebluealliance.com",
    )


def make_media(team_num: TeamNumber, year: int) -> List[Media]:
    return [
        Media(
            id="imgur_HSHpnyg",
            media_type_enum=MediaType.IMGUR,
            foreign_key="HSHpnyg",
            details_json=json.dumps({}),
            references=[ndb.Key(Team, f"frc{team_num}")],
            preferred_references=[ndb.Key(Team, f"frc{team_num}")],
            year=year,
        ),
        Media(
            id="imgur_MdhOTCR",
            media_type_enum=MediaType.IMGUR,
            foreign_key="MdhOTCR",
            details_json=json.dumps({}),
            references=[ndb.Key(Team, f"frc{team_num}")],
            preferred_references=[ndb.Key(Team, f"frc{team_num}")],
            year=year,
        ),
    ]


def make_event(event_key: EventKey) -> Event:
    return Event(
        id=event_key,
        year=int(event_key[:4]),
        timezone_id="America/New_York",
        name=f"Regional: {event_key}",
        short_name="New York City",
        event_short=event_key[4:],
        event_type_enum=EventType.REGIONAL,
        official=True,
        playoff_type=PlayoffType.BRACKET_8_TEAM,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json="[]",
    )


def make_eventteam(event_key: EventKey, team_key: TeamKey) -> EventTeam:
    return EventTeam(
        id=f"{event_key}_{team_key}",
        event=ndb.Key(Event, event_key),
        team=ndb.Key(Team, team_key),
        year=int(event_key[:4]),
    )


def make_match(match_key: MatchKey) -> Match:
    event_key, _ = match_key.split("_")
    return Match(
        id=match_key,
        event=ndb.Key(Event, event_key),
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc1", "frc2", "frc3"],
                    score=-1,
                    surrogates=[],
                    dqs=[],
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc4", "frc5", "frc6"],
                    score=-1,
                    surrogates=[],
                    dqs=[],
                ),
            }
        ),
        score_breakdown_json=None,
        comp_level=CompLevel.QM,
        year=int(event_key[:4]),
        set_number=1,
        match_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        youtube_videos=[],
    )


def mock_team_detail_url(m: RequestsMocker, team: Team) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/team/{team.key_name}",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=TeamConverter(team).convert(ApiMajorVersion.API_V3),
    )


def mock_team_media_url(
    m: RequestsMocker, team: Team, media: List[Media], year: int
) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/team/{team.key_name}/media/{year}",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=MediaConverter(media).convert(ApiMajorVersion.API_V3),
    )


def mock_match_detail_url(m: RequestsMocker, match: Match) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/match/{match.key_name}",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=MatchConverter(match).convert(ApiMajorVersion.API_V3),
    )


def mock_match_zebra_url(m: RequestsMocker, match: Match) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/match/{match.key_name}/zebra_motionworks",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json={"key": match.key_name},
    )


def mock_event_detail_url(m: RequestsMocker, event: Event) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/event/{event.key_name}",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=EventConverter(event).convert(ApiMajorVersion.API_V3),
    )


def mock_event_teams_url(
    m: RequestsMocker, event_key: EventKey, teams: List[Team]
) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/event/{event_key}/teams",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=TeamConverter(teams).convert(ApiMajorVersion.API_V3),
    )


def mock_event_matches_url(
    m: RequestsMocker, event_key: EventKey, matches: List[Match]
) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/event/{event_key}/matches",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=MatchConverter(matches).convert(ApiMajorVersion.API_V3),
    )


def mock_event_rankings_url(
    m: RequestsMocker, event_key: EventKey, rankings: List[EventRanking]
) -> None:
    details = EventDetailsConverter(
        EventDetails(id=event_key, rankings2=rankings)
    ).convert(ApiMajorVersion.API_V3)
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/event/{event_key}/rankings",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=cast(Dict, details)["rankings"] if details else {},
    )


def mock_event_alliances_url(
    m: RequestsMocker, event_key: EventKey, alliances: List[EventAlliance]
) -> None:
    details = EventDetailsConverter(
        EventDetails(id=event_key, alliance_selections=alliances)
    ).convert(ApiMajorVersion.API_V3)
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/event/{event_key}/alliances",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=cast(Dict, details)["alliances"],
    )


def mock_event_awards_url(
    m: RequestsMocker, event_key: EventKey, awards: List[Award]
) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/event/{event_key}/awards",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=AwardConverter(awards).convert(ApiMajorVersion.API_V3),
    )


def mock_events_url(m: RequestsMocker, year: Year, events: List[Event]) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/events/{year}",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        json=[
            EventConverter(event).convert(ApiMajorVersion.API_V3) for event in events
        ],
    )


def mock_event_predictions_url(
    m: RequestsMocker, event_key: EventKey, predictions: EventPredictions
) -> None:
    m.register_uri(
        "GET",
        f"https://www.thebluealliance.com/api/v3/event/{event_key}/predictions",
        headers={"X-TBA-Auth-Key": "test_apiv3"},
        status_code=200,
        json=predictions,
    )


def test_bootstrap_unknown_key() -> None:
    resp = LocalDataBootstrap.bootstrap_key("asdf", "asdf")
    assert resp is None


def test_bootstrap_team(
    ndb_context, requests_mock: RequestsMocker, taskqueue_stub
) -> None:
    team = make_team(254)
    mock_team_detail_url(requests_mock, team)

    year = datetime.now().year
    media = make_media(254, year)
    mock_team_media_url(requests_mock, team, media, year)

    resp = LocalDataBootstrap.bootstrap_key("frc254", "test_apiv3")
    assert resp == "/team/254"

    stored_team = Team.get_by_id("frc254")
    assert team == remove_auto_add_properties(stored_team)

    stored_media1 = Media.get_by_id("imgur_HSHpnyg")
    assert media[0] == remove_auto_add_properties(stored_media1)
    stored_media2 = Media.get_by_id("imgur_MdhOTCR")
    assert media[1] == remove_auto_add_properties(stored_media2)


def test_bootstrap_match(
    ndb_context, requests_mock: RequestsMocker, taskqueue_stub
) -> None:
    match = make_match("2020nyny_qm1")
    mock_match_detail_url(requests_mock, match)
    mock_match_zebra_url(requests_mock, match)

    resp = LocalDataBootstrap.bootstrap_key("2020nyny_qm1", "test_apiv3")
    assert resp == "/match/2020nyny_qm1"

    stored_match = Match.get_by_id("2020nyny_qm1")
    assert match == remove_auto_add_properties(stored_match)


def test_bootstrap_event(
    ndb_context, requests_mock: RequestsMocker, taskqueue_stub
) -> None:
    event = make_event("2020nyny")
    # Add remap_teams data to test the field
    remap_teams = {"frc9999": "frc254B", "frc9998": "frc118"}
    event.remap_teams = remap_teams
    team1 = make_team(254)
    team2 = make_team(255)
    match = make_match("2020nyny_qm1")
    rankings = [
        EventRanking(
            rank=1,
            team_key="frc254",
            record=None,
            qual_average=None,
            matches_played=0,
            dq=0,
            sort_orders=[0],
        )
    ]
    alliances = [EventAlliance(picks=["frc1", "frc2", "frc3"])]
    award = Award(
        id="2020nyny_0",
        name_str="Chairmans",
        award_type_enum=AwardType.CHAIRMANS,
        event=ndb.Key(Event, "2020nyny"),
        event_type_enum=EventType.REGIONAL,
        year=2020,
        team_list=[],
    )
    mock_event_detail_url(requests_mock, event)
    mock_event_teams_url(requests_mock, event.key_name, [team1, team2])
    mock_event_matches_url(requests_mock, event.key_name, [match])
    mock_event_rankings_url(requests_mock, event.key_name, rankings)
    mock_event_alliances_url(requests_mock, event.key_name, alliances)
    mock_event_awards_url(requests_mock, event.key_name, [award])
    mock_event_predictions_url(
        requests_mock,
        event.key_name,
        {
            "match_predictions": None,
            "match_prediction_stats": None,
            "stat_mean_vars": None,
            "ranking_predictions": None,
            "ranking_prediction_stats": None,
        },
    )

    resp = LocalDataBootstrap.bootstrap_key("2020nyny", "test_apiv3")
    assert resp == "/event/2020nyny"

    stored_event = Event.get_by_id("2020nyny")
    assert event == remove_auto_add_properties(stored_event)
    assert stored_event.remap_teams == remap_teams

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

    stored_match = Match.get_by_id("2020nyny_qm1")
    assert match == remove_auto_add_properties(stored_match)

    stored_details = EventDetails.get_by_id("2020nyny")
    expected_details = EventDetails(
        id="2020nyny",
        rankings2=rankings,
        alliance_selections=alliances,
        predictions={
            "match_predictions": None,
            "match_prediction_stats": None,
            "stat_mean_vars": None,
            "ranking_predictions": None,
            "ranking_prediction_stats": None,
        },
    )
    assert expected_details == remove_auto_add_properties(stored_details)

    stored_award = Award.get_by_id("2020nyny_0")
    assert award == remove_auto_add_properties(stored_award)


def test_bootstrap_year(
    ndb_context, requests_mock: RequestsMocker, taskqueue_stub
) -> None:
    # Assert no tasks in the queue
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0

    e1 = make_event("2020miket")
    e2 = make_event("2020mike2")
    mock_events_url(requests_mock, 2020, [e1, e2])

    for event in [e1, e2]:
        mock_event_detail_url(requests_mock, event)
        mock_event_teams_url(requests_mock, event.key_name, [])
        mock_event_matches_url(requests_mock, event.key_name, [])
        mock_event_rankings_url(requests_mock, event.key_name, [])
        mock_event_alliances_url(requests_mock, event.key_name, [])
        mock_event_awards_url(requests_mock, event.key_name, [])
        mock_event_predictions_url(
            requests_mock,
            event.key_name,
            {
                "match_predictions": None,
                "match_prediction_stats": None,
                "stat_mean_vars": None,
                "ranking_predictions": None,
                "ranking_prediction_stats": None,
            },
        )

    resp = LocalDataBootstrap.bootstrap_key("2020", "test_apiv3")
    assert resp == "/events/2020"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 2

    for task in tasks:
        run_from_task(task)

    stored_e1 = Event.get_by_id("2020miket")
    assert e1 == remove_auto_add_properties(stored_e1)

    stored_e2 = Event.get_by_id("2020mike2")
    assert e2 == remove_auto_add_properties(stored_e2)


def test_bootstrap_event_with_district(
    ndb_context, requests_mock: RequestsMocker, taskqueue_stub
) -> None:
    district = District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
    )
    district.put()
    event = make_event("2020nyny")
    event.district_key = ndb.Key(District, "2020ne")

    mock_event_detail_url(requests_mock, event)
    mock_event_teams_url(requests_mock, event.key_name, [])
    mock_event_matches_url(requests_mock, event.key_name, [])
    mock_event_rankings_url(requests_mock, event.key_name, [])
    mock_event_alliances_url(requests_mock, event.key_name, [])
    mock_event_awards_url(requests_mock, event.key_name, [])
    mock_event_predictions_url(
        requests_mock,
        event.key_name,
        {
            "match_predictions": None,
            "match_prediction_stats": None,
            "stat_mean_vars": None,
            "ranking_predictions": None,
            "ranking_prediction_stats": None,
        },
    )

    resp = LocalDataBootstrap.bootstrap_key("2020nyny", "test_apiv3")
    assert resp == "/event/2020nyny"

    stored_event = Event.get_by_id("2020nyny")
    assert event == remove_auto_add_properties(stored_event)
