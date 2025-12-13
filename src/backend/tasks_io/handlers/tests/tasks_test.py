import datetime
import urllib.parse
from unittest.mock import patch

from freezegun import freeze_time
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
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
    mock_blacklist.assert_called_with(website)

    redirect_url = urllib.parse.urlparse(resp.location)
    assert redirect_url.path == "/backend-tasks/get/team_details/frc7332"

    assert not none_throws(Team.get_by_id("frc7332")).website


@freeze_time("2025-01-01")
def test_archive_api_keys(tasks_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.MATCH_VIDEO],
        event_list=[ndb.Key(Event, "2024test")],
    ).put()

    resp = tasks_client.get("/tasks/do/archive_api_keys")
    assert resp.status_code == 200

    key = ApiAuthAccess.get_by_id("test_auth_key")
    assert key is not None
    assert key.expiration == datetime.datetime(year=2025, month=1, day=1)


@freeze_time("2025-01-01")
def test_archive_api_keys_ignores_read_keys(tasks_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    resp = tasks_client.get("/tasks/do/archive_api_keys")
    assert resp.status_code == 200

    key = ApiAuthAccess.get_by_id("test_auth_key")
    assert key is not None
    assert key.expiration is None


@freeze_time("2025-01-01")
def test_archive_api_keys_ignores_current_year_events(tasks_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.MATCH_VIDEO],
        event_list=[ndb.Key(Event, "2025test")],
    ).put()

    resp = tasks_client.get("/tasks/do/archive_api_keys")
    assert resp.status_code == 200

    key = ApiAuthAccess.get_by_id("test_auth_key")
    assert key is not None
    assert key.expiration is None


@freeze_time("2025-01-01")
def test_archive_api_keys_ignores_existing_expiration(tasks_client: Client) -> None:
    initial_expiration = datetime.datetime(year=2024, month=7, day=1)
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.MATCH_VIDEO],
        event_list=[ndb.Key(Event, "2024test")],
        expiration=initial_expiration,
    ).put()

    resp = tasks_client.get("/tasks/do/archive_api_keys")
    assert resp.status_code == 200

    key = ApiAuthAccess.get_by_id("test_auth_key")
    assert key is not None
    assert key.expiration == initial_expiration
