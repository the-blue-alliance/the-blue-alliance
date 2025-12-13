import json

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.handlers.tests.helpers import (
    validate_nominal_event_keys,
    validate_nominal_match_keys,
    validate_nominal_team_keys,
    validate_simple_event_keys,
    validate_simple_match_keys,
    validate_simple_team_keys,
)
from backend.common.consts.auth_type import AuthType
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_tag import MediaTag
from backend.common.consts.media_type import MediaType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.robot import Robot
from backend.common.models.team import Team


def test_team(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "frc254"
    validate_nominal_team_keys(resp.json)

    # Simple response
    resp = api_client.get(
        "/api/v3/team/frc254/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "frc254"
    validate_simple_team_keys(resp.json)

    # Keys response
    resp = api_client.get(
        "/api/v3/team/frc254/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404


def test_team_years_participated(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    EventTeam(
        id="1992casj_frc254",
        event=ndb.Key("Event", "1992casj"),
        team=ndb.Key("Team", "frc254"),
        year=1992,
    ).put()
    EventTeam(
        id="2010casj_frc254",
        event=ndb.Key("Event", "2010casj"),
        team=ndb.Key("Team", "frc254"),
        year=2010,
    ).put()
    EventTeam(
        id="2020casj_frc254",
        event=ndb.Key("Event", "2020casj"),
        team=ndb.Key("Team", "frc254"),
        year=2020,
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/years_participated",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == [1992, 2010, 2020]


def test_team_history_districts(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    District(
        id="2015fim",
        year=2015,
        abbreviation="fim",
    ).put()
    District(
        id="2020fim",
        year=2020,
        abbreviation="fim",
    ).put()
    DistrictTeam(
        id="2015fim_frc254",
        district_key=ndb.Key(District, "2015fim"),
        team=ndb.Key(Team, "frc254"),
        year=2015,
    ).put()
    DistrictTeam(
        id="2020fim_frc254",
        district_key=ndb.Key(District, "2020fim"),
        team=ndb.Key(Team, "frc254"),
        year=2020,
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/districts",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    district_keys = set([d["key"] for d in resp.json])
    assert "2015fim" in district_keys
    assert "2020fim" in district_keys


def test_team_history_robots(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Robot(
        id="frc254_2010",
        team=ndb.Key("Team", "frc254"),
        year=2010,
    ).put()
    Robot(
        id="frc254_2020",
        team=ndb.Key("Team", "frc254"),
        year=2020,
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/robots",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    robot_keys = set([d["key"] for d in resp.json])
    assert "frc254_2010" in robot_keys
    assert "frc254_2020" in robot_keys


def test_team_social_media(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Media(
        references=[ndb.Key("Team", "frc254")],
        year=None,
        media_type_enum=MediaType.FACEBOOK_PROFILE,
        foreign_key="test",
        details_json=None,
    ).put()
    Media(
        references=[ndb.Key("Team", "frc254")],
        year=None,
        media_type_enum=MediaType.GITHUB_PROFILE,
        foreign_key="test",
        details_json=None,
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/social_media",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_team_events(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    EventTeam(
        id="2019casj_frc254",
        event=ndb.Key("Event", "2019casj"),
        team=ndb.Key("Team", "frc254"),
        year=2019,
    ).put()
    EventTeam(
        id="2020casj_frc254",
        event=ndb.Key("Event", "2020casj"),
        team=ndb.Key("Team", "frc254"),
        year=2020,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/team/frc254/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_nominal_event_keys(event)

    # Simple response
    resp = api_client.get(
        "/api/v3/team/frc254/events/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_simple_event_keys(event)

    # Keys response
    resp = api_client.get(
        "/api/v3/team/frc254/events/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_team_events_statuses_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    EventTeam(
        id="2020casj_frc254",
        event=ndb.Key("Event", "2020casj"),
        team=ndb.Key("Team", "frc254"),
        year=2020,
    ).put()
    EventTeam(
        id="2020casf_frc254",
        event=ndb.Key("Event", "2020casf"),
        team=ndb.Key("Team", "frc254"),
        year=2020,
        status={},
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/events/2020/statuses",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert resp.json.get("2020casj") is None
    casf_status = resp.json.get("2020casf")
    assert casf_status is not None
    assert (
        casf_status["overall_status_str"]
        == "Team 254 is waiting for the event to begin."
    )


def test_team_events_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020casf",
        year=2020,
        event_short="casf",
        event_type_enum=EventType.REGIONAL,
    ).put()
    EventTeam(
        id="2019casj_frc254",
        event=ndb.Key("Event", "2019casj"),
        team=ndb.Key("Team", "frc254"),
        year=2019,
    ).put()
    EventTeam(
        id="2020casj_frc254",
        event=ndb.Key("Event", "2020casj"),
        team=ndb.Key("Team", "frc254"),
        year=2020,
    ).put()
    EventTeam(
        id="2020casf_frc254",
        event=ndb.Key("Event", "2020casf"),
        team=ndb.Key("Team", "frc254"),
        year=2020,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/team/frc254/events/2019", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for event in resp.json:
        validate_nominal_event_keys(event)

    resp = api_client.get(
        "/api/v3/team/frc254/events/2020", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_nominal_event_keys(event)

    # Simple response
    resp = api_client.get(
        "/api/v3/team/frc254/events/2019/simple",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for event in resp.json:
        validate_simple_event_keys(event)

    resp = api_client.get(
        "/api/v3/team/frc254/events/2020/simple",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_simple_event_keys(event)

    # Keys response
    resp = api_client.get(
        "/api/v3/team/frc254/events/2019/keys",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0] == "2019casj"

    resp = api_client.get(
        "/api/v3/team/frc254/events/2020/keys",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert "2020casj" in resp.json
    assert "2020casf" in resp.json


def test_team_event_matches(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
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
        team_key_names=["frc254"],
    ).put()
    Match(
        id="2020casj_qm2",
        year=2020,
        event=ndb.Key("Event", "2020casj"),
        comp_level="qm",
        match_number=2,
        set_number=1,
        alliances_json=json.dumps(
            {
                "red": {"score": 0, "teams": []},
                "blue": {"score": 0, "teams": []},
            }
        ),
        team_key_names=["frc254"],
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/team/frc254/event/2020casj/matches",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for match in resp.json:
        validate_nominal_match_keys(match)

    # Simple response
    resp = api_client.get(
        "/api/v3/team/frc254/event/2020casj/matches/simple",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for match in resp.json:
        validate_simple_match_keys(match)

    # Keys response
    resp = api_client.get(
        "/api/v3/team/frc254/event/2020casj/matches/keys",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert "2020casj_qm1" in resp.json
    assert "2020casj_qm2" in resp.json


def test_team_event_awards(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Award(
        id="2020casj_1",
        year=2020,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2020casj"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()
    Award(
        id="2020casj_2",
        year=2020,
        award_type_enum=AwardType.FINALIST,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2020casj"),
        name_str="Finalist",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/event/2020casj/awards",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    award_names = set([a["name"] for a in resp.json])
    assert "Winner" in award_names
    assert "Finalist" in award_names


def test_team_event_status(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    EventTeam(
        id="2020casj_frc254",
        event=ndb.Key("Event", "2020casj"),
        team=ndb.Key("Team", "frc254"),
        year=2020,
        status={},
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/event/2020casj/status",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert (
        resp.json["overall_status_str"] == "Team 254 is waiting for the event to begin."
    )


def test_team_awards(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Award(
        id="2019casj_1",
        year=2019,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2019casj"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()
    Award(
        id="2020casj_1",
        year=2020,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2020casj"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()
    Award(
        id="2020casj_2",
        year=2020,
        award_type_enum=AwardType.FINALIST,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2020casj"),
        name_str="Finalist",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()

    # All awards
    resp = api_client.get(
        "/api/v3/team/frc254/awards",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 3

    # 2019 awards
    resp = api_client.get(
        "/api/v3/team/frc254/awards/2019",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1

    # 2020 awards
    resp = api_client.get(
        "/api/v3/team/frc254/awards/2020",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_team_year_matches(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
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
        team_key_names=["frc254"],
    ).put()
    Match(
        id="2020casj_qm2",
        year=2020,
        event=ndb.Key("Event", "2020casj"),
        comp_level="qm",
        match_number=2,
        set_number=1,
        alliances_json=json.dumps(
            {
                "red": {"score": 0, "teams": []},
                "blue": {"score": 0, "teams": []},
            }
        ),
        team_key_names=["frc254"],
    ).put()

    # Null response
    resp = api_client.get(
        "/api/v3/team/frc254/matches/2019",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Nominal response
    resp = api_client.get(
        "/api/v3/team/frc254/matches/2020",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for match in resp.json:
        validate_nominal_match_keys(match)

    # Simple response
    resp = api_client.get(
        "/api/v3/team/frc254/matches/2020/simple",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for match in resp.json:
        validate_simple_match_keys(match)

    # Keys response
    resp = api_client.get(
        "/api/v3/team/frc254/matches/2020/keys",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert "2020casj_qm1" in resp.json
    assert "2020casj_qm2" in resp.json


def test_team_media_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Media(
        references=[ndb.Key("Team", "frc254")],
        year=2020,
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="test1",
        details_json="{}",
    ).put()
    Media(
        references=[ndb.Key("Team", "frc254")],
        year=2020,
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="test2",
        details_json="{}",
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/media/2020",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_team_media_tag(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Media(
        references=[ndb.Key("Team", "frc254")],
        year=2019,
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        media_tag_enum=[MediaTag.CHAIRMANS_VIDEO],
        foreign_key="test1",
        details_json="{}",
    ).put()
    Media(
        references=[ndb.Key("Team", "frc254")],
        year=2020,
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        media_tag_enum=[MediaTag.CHAIRMANS_VIDEO],
        foreign_key="test2",
        details_json="{}",
    ).put()
    Media(
        references=[ndb.Key("Team", "frc254")],
        year=2020,
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        media_tag_enum=[MediaTag.CHAIRMANS_PRESENTATION],
        foreign_key="test3",
        details_json="{}",
    ).put()

    # Bad tag
    resp = api_client.get(
        "/api/v3/team/frc254/media/tag/bad_tag",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # All years
    resp = api_client.get(
        "/api/v3/team/frc254/media/tag/chairmans_video",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2

    # Single year
    resp = api_client.get(
        "/api/v3/team/frc254/media/tag/chairmans_video/2020",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["foreign_key"] == "test2"

    resp = api_client.get(
        "/api/v3/team/frc254/media/tag/chairmans_presentation/2020",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0]["foreign_key"] == "test3"


def test_team_list_all(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc67", team_number=67).put()
    Team(id="frc254", team_number=254).put()
    Team(id="frc604", team_number=604).put()
    Team(id="frc9999", team_number=9999).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/teams/all", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 4
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"
    assert resp.json[2]["key"] == "frc604"
    assert resp.json[3]["key"] == "frc9999"

    # Simple response
    resp = api_client.get(
        "/api/v3/teams/all/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 4
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"
    assert resp.json[2]["key"] == "frc604"
    assert resp.json[3]["key"] == "frc9999"

    # Keys response
    resp = api_client.get(
        "/api/v3/teams/all/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 4
    assert resp.json[0] == "frc67"
    assert resp.json[1] == "frc254"
    assert resp.json[2] == "frc604"
    assert resp.json[3] == "frc9999"


def test_team_list(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc67", team_number=67).put()
    Team(id="frc254", team_number=254).put()
    Team(id="frc604", team_number=604).put()
    Team(id="frc9999", team_number=9999).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/teams/0", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/1", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc604"

    resp = api_client.get(
        "/api/v3/teams/2", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Simple response
    resp = api_client.get(
        "/api/v3/teams/0/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/1/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc604"

    resp = api_client.get(
        "/api/v3/teams/2/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Keys response
    resp = api_client.get(
        "/api/v3/teams/0/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert resp.json[0] == "frc67"
    assert resp.json[1] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/1/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0] == "frc604"

    resp = api_client.get(
        "/api/v3/teams/2/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0


def test_team_list_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc67", team_number=67).put()
    Team(id="frc254", team_number=254).put()
    EventTeam(
        id="2020casj_frc67",
        event=ndb.Key("Event", "2020casj"),
        team=ndb.Key("Team", "frc67"),
        year=2020,
    ).put()
    EventTeam(
        id="2019casj_frc254",
        event=ndb.Key("Event", "2019casj"),
        team=ndb.Key("Team", "frc254"),
        year=2019,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/teams/2020/0", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc67"

    resp = api_client.get(
        "/api/v3/teams/2019/0", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/2018/0", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Simple response
    resp = api_client.get(
        "/api/v3/teams/2020/0/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc67"

    resp = api_client.get(
        "/api/v3/teams/2019/0/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/2018/0/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Keys response
    resp = api_client.get(
        "/api/v3/teams/2020/0/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0] == "frc67"

    resp = api_client.get(
        "/api/v3/teams/2019/0/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/2018/0/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0


def test_team_history(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Award(
        id="2020casj_1",
        year=2020,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2020casj"),
        name_str="Winner",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()
    Award(
        id="2020casj_2",
        year=2020,
        award_type_enum=AwardType.FINALIST,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2020casj"),
        name_str="Finalist",
        team_list=[ndb.Key(Team, "frc254")],
    ).put()

    EventTeam(
        id="2020casj_frc254",
        event=ndb.Key("Event", "2020casj"),
        team=ndb.Key("Team", "frc254"),
        year=2020,
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/history",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200

    assert "awards" in resp.json
    assert resp.json["awards"] == [
        {
            "award_type": 1,
            "event_key": "2020casj",
            "name": "Winner",
            "recipient_list": [],
            "year": 2020,
        },
        {
            "award_type": 2,
            "event_key": "2020casj",
            "name": "Finalist",
            "recipient_list": [],
            "year": 2020,
        },
    ]

    assert "events" in resp.json
    assert len(resp.json["events"]) == 1
    assert resp.json["events"][0]["key"] == "2020casj"
