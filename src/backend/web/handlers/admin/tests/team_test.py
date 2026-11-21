import json
from unittest.mock import patch

import bs4
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.media_type import MediaType
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.media import Media
from backend.common.models.regional_pool_team import RegionalPoolTeam
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.sitevars.website_blocklist import WebsiteBlocklist
from backend.web.handlers.tests import helpers


def test_team_detail_has_audit_logs_link(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_team(1124)

    resp = web_client.get("/admin/team/1124")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    audit_logs_link = soup.find("a", href="/admin/audit_logs?key=Team:frc1124")
    assert audit_logs_link is not None


# ---------------------------------------------------------------------------
# /admin/teams[/<page_num>]
# ---------------------------------------------------------------------------


def test_team_list_first_page(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_team(254)
    helpers.preseed_team(1124)
    helpers.preseed_team(10123)

    resp = web_client.get("/admin/teams")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "/admin/team/254" in content
    assert "/admin/team/1124" not in content
    assert "/admin/team/10123" not in content


def test_team_list_middle_page(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_team(254)
    helpers.preseed_team(1124)
    helpers.preseed_team(10123)

    resp = web_client.get("/admin/teams/1")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "/admin/team/254" not in content
    assert "/admin/team/1124" in content
    assert "/admin/team/10123" not in content


def test_team_list_last_page_shows_everything_above_max(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_team(254)
    helpers.preseed_team(10123)
    helpers.preseed_team(25000)

    resp = web_client.get("/admin/teams/10")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "/admin/team/254" not in content
    assert "/admin/team/10123" in content
    assert "/admin/team/25000" in content


# ---------------------------------------------------------------------------
# /admin/team/<team_number>
# ---------------------------------------------------------------------------


def test_team_detail_not_found(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/team/1124")
    assert resp.status_code == 404


def test_team_detail_with_related_models(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_team(1124)
    team_key = ndb.Key(Team, "frc1124")

    EventTeam(
        id="2019nyny_frc1124",
        event=ndb.Key(Event, "2019nyny"),
        team=team_key,
        year=2019,
    ).put()
    Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        year=2019,
        references=[team_key],
    ).put()
    Media(
        id="cdphotothread_123",
        media_type_enum=MediaType.CD_PHOTO_THREAD,
        foreign_key="123",
        details_json=json.dumps({"image_partial": "abc_l.jpg"}),
        year=2018,
        references=[team_key],
    ).put()
    Media(
        id="github-profile_frc1124",
        media_type_enum=MediaType.GITHUB_PROFILE,
        foreign_key="frc1124",
        references=[team_key],
    ).put()
    Robot(id="frc1124_2019", team=team_key, year=2019, robot_name="Robo").put()
    DistrictTeam(
        id="2019ne_frc1124",
        team=team_key,
        year=2019,
        district_key=ndb.Key(District, "2019ne"),
    ).put()
    RegionalPoolTeam(id="2025_frc1124", team=team_key, year=2025).put()

    resp = web_client.get("/admin/team/1124")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "Robo" in content
    assert "2019ne" in content
    assert "github" in content.lower()


# ---------------------------------------------------------------------------
# /admin/team/set_robot_name
# ---------------------------------------------------------------------------


def test_team_robot_name_update_team_not_found(
    web_client: Client, login_gae_admin
) -> None:
    resp = web_client.post(
        "/admin/team/set_robot_name",
        data={"team_key": "frc1124", "robot_year": "2019", "robot_name": "Robo"},
    )
    assert resp.status_code == 404


def test_team_robot_name_update_missing_name(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_team(1124)
    resp = web_client.post(
        "/admin/team/set_robot_name",
        data={"team_key": "frc1124", "robot_year": "2019", "robot_name": ""},
    )
    assert resp.status_code == 400
    assert Robot.get_by_id("frc1124_2019") is None


def test_team_robot_name_update_zero_year(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_team(1124)
    resp = web_client.post(
        "/admin/team/set_robot_name",
        data={"team_key": "frc1124", "robot_year": "0", "robot_name": "Robo"},
    )
    assert resp.status_code == 400


def test_team_robot_name_update(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_team(1124)
    resp = web_client.post(
        "/admin/team/set_robot_name",
        data={"team_key": "frc1124", "robot_year": "2019", "robot_name": "  Robo  "},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/team/1124"

    robot = Robot.get_by_id("frc1124_2019")
    assert robot is not None
    assert robot.team == ndb.Key(Team, "frc1124")
    assert robot.year == 2019
    assert robot.robot_name == "Robo"


# ---------------------------------------------------------------------------
# /admin/team/website
# ---------------------------------------------------------------------------


def test_team_website_update_team_not_found(
    web_client: Client, login_gae_admin
) -> None:
    resp = web_client.post(
        "/admin/team/website",
        data={"team_key": "frc1124", "website": "https://example.com"},
    )
    assert resp.status_code == 404


def test_team_website_update_clears_website(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_team(1124)
    resp = web_client.post(
        "/admin/team/website",
        data={"team_key": "frc1124", "website": ""},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/team/1124"

    team = Team.get_by_id("frc1124")
    assert team is not None
    assert team.website == ""


def test_team_website_update_sets_valid_url(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_team(1124)
    resp = web_client.post(
        "/admin/team/website",
        data={"team_key": "frc1124", "website": "https://example.com/team"},
    )
    assert resp.status_code == 302

    team = Team.get_by_id("frc1124")
    assert team is not None
    assert team.website == "https://example.com/team"


def test_team_website_update_ignores_invalid_url(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_team(1124)
    resp = web_client.post(
        "/admin/team/website",
        data={"team_key": "frc1124", "website": "not a url"},
    )
    assert resp.status_code == 302

    team = Team.get_by_id("frc1124")
    assert team is not None
    assert team.website == "https://www.thebluealliance.com"


def test_team_website_update_ignores_blocklisted_url(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_team(1124)
    WebsiteBlocklist.blacklist("https://spam.example.com")

    resp = web_client.post(
        "/admin/team/website",
        data={"team_key": "frc1124", "website": "https://spam.example.com"},
    )
    assert resp.status_code == 302

    team = Team.get_by_id("frc1124")
    assert team is not None
    assert team.website == "https://www.thebluealliance.com"


def test_team_detail_media_years_sorted_newest_first(
    web_client: Client, login_gae_admin
) -> None:
    """Admin team_detail lists media years newest first."""
    helpers.preseed_team(1124)
    team_key = ndb.Key(Team, "frc1124")
    # Keys chosen so the query returns the older year first.
    Media(
        id="cdphotothread_a",
        media_type_enum=MediaType.CD_PHOTO_THREAD,
        foreign_key="a",
        details_json=json.dumps({"image_partial": "a_l.jpg"}),
        year=2018,
        references=[team_key],
    ).put()
    Media(
        id="youtube_b",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="b",
        year=2019,
        references=[team_key],
    ).put()

    with patch(
        "backend.web.handlers.admin.team.render_template", return_value="ok"
    ) as mock_render:
        resp = web_client.get("/admin/team/1124")

    assert resp.status_code == 200
    template_values = mock_render.call_args[0][1]
    assert template_values["team_media_years"] == [2019, 2018]
