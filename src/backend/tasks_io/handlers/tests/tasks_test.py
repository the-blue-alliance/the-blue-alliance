import urllib.parse
from unittest.mock import patch

from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.models.team import Team
from backend.common.sitevars.website_blacklist import WebsiteBlacklist


def test_blacklist_website_invalid_key(tasks_client: Client):
    resp = tasks_client.get("/backend-tasks/do/team_blacklist_website/1")
    assert resp.status_code == 400
    assert resp.data == b"Bad team key: 1"


def test_blacklist_website_no_team(tasks_client: Client):
    resp = tasks_client.get("/backend-tasks/do/team_blacklist_website/frc7332")
    assert resp.status_code == 302

    redirect_url = urllib.parse.urlparse(resp.location)
    assert redirect_url.path == "/backend-tasks/get/team_details/frc7332"


def test_blacklist_website_team(tasks_client: Client):
    website = "https://www.thebluealliance.com"

    team = Team(id="frc7332", team_number=7332, website=website)
    team.put()

    assert team.website == website

    with patch.object(WebsiteBlacklist, "blacklist") as mock_blacklist:
        resp = tasks_client.get("/backend-tasks/do/team_blacklist_website/frc7332")

    assert resp.status_code == 302
    assert mock_blacklist.called_with(website)

    redirect_url = urllib.parse.urlparse(resp.location)
    assert redirect_url.path == "/backend-tasks/get/team_details/frc7332"

    assert not none_throws(Team.get_by_id("frc7332")).website
