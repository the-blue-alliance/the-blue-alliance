from typing import cast, List
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from werkzeug.test import Client

from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.common.models.team import Team
from backend.web.handlers.conftest import CapturedTemplate


@pytest.fixture(autouse=True)
def storeTeam(ndb_stub):
    team = Team(
        id="frc1124",
        team_number=1124,
    )
    team.put()


def assert_template_status(
    captured_templates: List[CapturedTemplate], status: str
) -> None:
    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "suggestions/suggest_team_media.html"
    assert context["status"] == status


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/team/media?team_key=frc1124&year=2016")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_get_no_team(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/team/media")
    assert response.status_code == 404


def test_get_bad_team(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/team/media?team_key=frc254&year=2016")
    assert response.status_code == 404


def test_get_bad_year(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/team/media?team_key=frc1124&year=asdf")
    assert response.status_code == 404


def test_get_form(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/team/media?team_key=frc1124&year=2016")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form", id="suggest_media")
    assert form is not None
    assert form["action"] == "/suggest/team/media"
    assert form["method"] == "post"

    csrf = form.find(attrs={"name": "csrf_token"})
    assert csrf is not None
    assert csrf["type"] == "hidden"
    assert csrf["value"] is not None

    team_key = form.find(attrs={"name": "team_key"})
    assert team_key is not None
    assert team_key["type"] == "hidden"
    assert team_key["value"] == "frc1124"

    year = form.find(attrs={"name": "year"})
    assert year is not None
    assert year["type"] == "hidden"
    assert year["value"] == "2016"

    assert form.find(attrs={"name": "media_url"}) is not None


def test_submit_no_team(login_user, ndb_stub, web_client: Client) -> None:
    resp = web_client.post("/suggest/team/media", data={})
    assert resp.status_code == 404

    # Assert no suggestions were written
    assert Suggestion.query().fetch() == []


def test_submit_bad_team(login_user, ndb_stub, web_client: Client) -> None:
    response = web_client.post(
        "/suggest/team/media",
        data={"team_key": "frc254", "year": "2016"},
        follow_redirects=True,
    )
    assert response.status_code == 404

    # Assert no suggestions were written
    assert Suggestion.query().fetch() == []


def test_submit_empty_form(
    login_user,
    ndb_stub,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/team/media",
        data={"team_key": "frc1124", "year": "2016", "media_url": ""},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "bad_url")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="bad_url-alert") is not None

    # Assert no suggestions were written
    assert Suggestion.query().fetch() == []


def test_suggest_media(
    login_user,
    ndb_stub,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/team/media",
        data={
            "team_key": "frc1124",
            "year": "2016",
            "media_url": "http://imgur.com/aF8T5ZE",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "success")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="success-alert") is not None

    # Make sure the Suggestion gets created
    suggestion = cast(Suggestion, Suggestion.query().fetch()[0])
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING
    assert suggestion.target_key == "frc1124"
    assert suggestion.contents == SuggestionDict(
        year=2016,
        reference_type="team",
        reference_key="frc1124",
        foreign_key="aF8T5ZE",
        is_social=False,
        media_type_enum=MediaType.IMGUR,
        default_preferred=False,
        site_name="Imgur Image",
    )
