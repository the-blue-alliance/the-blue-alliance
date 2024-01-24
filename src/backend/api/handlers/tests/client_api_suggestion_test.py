import json

from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.api.client_api_types import MediaSuggestionMessage
from backend.api.handlers.tests.clientapi_test_helper import make_clientapi_request
from backend.common.models.suggestion import Suggestion
from backend.common.models.user import User
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)


def test_suggest_no_auth(api_client: Client) -> None:
    req = MediaSuggestionMessage(
        reference_type="",
        reference_key="",
        year=2023,
        media_url="",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 401


def test_suggest_bad_reference_type(
    api_client: Client, mock_clientapi_auth: User
) -> None:
    req = MediaSuggestionMessage(
        reference_type="event",
        reference_key="",
        year=2023,
        media_url="",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 400


def test_suggest_bad_year(api_client: Client, mock_clientapi_auth: User) -> None:
    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="",
        year=1800,
        media_url="",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 400


def test_suggest_bad_url(api_client: Client, mock_clientapi_auth: User) -> None:
    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="frc1124",
        year=2016,
        media_url="http://example.com",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 400


def test_suggest_success(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="frc1124",
        year=2016,
        media_url="http://imgur.com/ruRAxDm",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 200

    suggestion_id = Suggestion.render_media_key_name(
        2016, "team", "frc1124", "imgur", "ruRAxDm"
    )
    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.author == mock_clientapi_auth.account_key


def test_suggest_already_exists(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    status, _ = SuggestionCreator.createTeamMediaSuggestion(
        none_throws(mock_clientapi_auth.account_key),
        "http://imgur.com/ruRAxDm",
        "frc1124",
        "2016",
    )
    assert status == SuggestionCreationStatus.SUCCESS

    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="frc1124",
        year=2016,
        media_url="http://imgur.com/ruRAxDm",
        details_json="",
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 304


def test_suggest_keeps_deletehash_private(
    api_client: Client, mock_clientapi_auth: User, ndb_stub
) -> None:
    req = MediaSuggestionMessage(
        reference_type="team",
        reference_key="frc1124",
        year=2016,
        media_url="http://imgur.com/ruRAxDm",
        details_json=json.dumps({"deletehash": "supersecret"}),
    )
    resp = make_clientapi_request(api_client, "/team/media/suggest", req)
    assert resp["code"] == 200

    suggestion_id = Suggestion.render_media_key_name(
        2016, "team", "frc1124", "imgur", "ruRAxDm"
    )
    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None

    suggestion_constents = suggestion.contents
    assert "private_details_json" in suggestion_constents
    assert suggestion_constents["private_details_json"] == json.dumps(
        {"deletehash": "supersecret"}
    )
