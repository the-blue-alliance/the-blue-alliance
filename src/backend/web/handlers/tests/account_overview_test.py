import datetime
from random import randint
from typing import List
from unittest.mock import ANY, Mock, patch
from urllib.parse import parse_qsl, urlparse

import bs4
import pytest
from flask import Flask
from flask.testing import FlaskClient

from backend.common.consts.auth_type import (
    AuthType,
    WRITE_TYPE_NAMES as AUTH_TYPE_WRITE_TYPE_NAMES,
)
from backend.common.sitevars.notifications_enable import NotificationsEnable
from backend.web.handlers.account import blueprint
from backend.web.handlers.conftest import CapturedTemplate
from backend.web.handlers.tests.helpers import assert_alert, get_page_title


def test_blueprint() -> None:
    assert blueprint.name == "account"
    assert blueprint.url_prefix == "/account"

    app = Flask(__name__)
    app.register_blueprint(blueprint)

    rules = list(app.url_map.iter_rules())
    # Remove static rule
    rules = [r for r in rules if r.endpoint != "static"]

    rules_map = {str(rule): rule.endpoint for rule in rules}
    assert rules_map == {
        "/account/api/read_key_add": "account.read_key_add",
        "/account/api/read_key_delete": "account.read_key_delete",
        "/account/delete": "account.delete",
        "/account/register": "account.register",
        "/account/logout": "account.logout",
        "/account/login": "account.login",
        "/account/edit": "account.edit",
        "/account/mytba": "account.mytba",
        "/account/mytba/team/<int:team_number>": "account.mytba_team_post",
        "/account/mytba/event/<string:event_key>": "account.mytba_event_post",
        "/account/mytba/eventteam/<int:team_number>": "account.mytba_eventteam_post",
        "/account": "account.overview",
        "/account/ping": "account.ping",
    }


def test_overview_logged_out(web_client: FlaskClient) -> None:
    response = web_client.get("/account")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account"
    }


def test_overview_unregistered(login_user, web_client: FlaskClient) -> None:
    login_user.is_registered = False

    response = web_client.get("/account")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/register"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account"
    }


def test_overview(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert get_page_title(response.data) == "Account Overview - The Blue Alliance"

    context_keys = {
        "status",
        "webhook_verification_success",
        "ping_sent",
        "ping_enabled",
        "auth_write_type_names",
        "user",
    }
    assert set(context_keys) <= set(context)


@pytest.mark.parametrize(
    "status, message, success",
    [
        ("account_edit_success", "Your profile has been updated.", True),
        (
            "read_key_add_success",
            "A new read API key has been successfully added.",
            True,
        ),
        (
            "read_key_add_no_description",
            "You must specify a description when adding a read API key. Please try again.",
            False,
        ),
        (
            "read_key_add_failure",
            "Unable to add a read API key. If this problem persists, please contact us.",
            False,
        ),
        (
            "read_key_delete_success",
            "The selected read API key has been deleted.",
            True,
        ),
        (
            "read_key_delete_failure",
            "Unable to delete the specified read API key. If this problem persists, please contact us.",
            False,
        ),
    ],
)
def test_overview_status(
    login_user,
    status: str,
    message: str,
    success: bool,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    with web_client:
        with web_client.session_transaction() as session:
            session["account_status"] = status
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["status"] == status

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    status_row = soup.find(id="status-row", attrs={"class": "row"})
    status = status_row.find("div", attrs={"class": "alert"})
    assert_alert(status, ("Success!" if success else "Oops!"), message, success)


def test_overview_no_status(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["status"] is None

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    status_row = soup.find(id="status-row", attrs={"class": "row"})
    assert status_row is None


def test_overview_webhook_verification_success(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    webhook_verification_success = "1"

    response = web_client.get(
        "/account?webhook_verification_success={}".format(webhook_verification_success)
    )

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["webhook_verification_success"] == webhook_verification_success

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    webhook_row = soup.find(id="webhook-row", attrs={"class": "row"})
    webhook_alert = webhook_row.find("div", attrs={"class": "alert"})
    assert_alert(
        webhook_alert, "Success!", "The webhook has been properly verified!", True
    )


def test_overview_no_webhook_verification_success(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["webhook_verification_success"] is None

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    webhook_row = soup.find(id="webhook-row", attrs={"class": "row"})
    assert webhook_row is None


@pytest.mark.parametrize("ping_sent, success", [("1", True), ("0", False)])
def test_overview_ping_sent(
    login_user,
    ping_sent: str,
    success: bool,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    with web_client:
        with web_client.session_transaction() as session:
            session["ping_sent"] = ping_sent
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["ping_sent"] == ping_sent

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    ping_row = soup.find(id="ping-row", attrs={"class": "row"})
    ping_alert = ping_row.find("div", attrs={"class": "alert"})
    assert_alert(
        ping_alert,
        ("Success!" if success else "Failure"),
        ("Ping was sent." if success else "Failed to send ping."),
        success,
    )


def test_overview_no_ping_sent(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["ping_sent"] is None

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    ping_row = soup.find(id="ping-row", attrs={"class": "row"})
    assert ping_row is None


def test_ping_enabled(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    # Add a dummy client so we have something to ping, to check that the ping rows are disabled
    login_user.mobile_clients = [Mock()]

    with patch.object(NotificationsEnable, "notifications_enabled", return_value=True):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    ping_button = soup.find("button", attrs={"class": "ping"})
    assert "disabled" not in list(ping_button.attrs)


def test_ping_disabled(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    # Add a dummy client so we have something to ping, to check that the ping rows are disabled
    login_user.mobile_clients = [Mock()]

    with patch.object(NotificationsEnable, "notifications_enabled", return_value=False):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    ping_button_disabled = soup.find("button", attrs={"class": "ping", "disabled": ""})
    assert ping_button_disabled


def test_num_favorites(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    favorites_count = randint(1, 100)

    login_user.favorites_count = favorites_count

    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    mytba_favorites_row = soup.find(id="mytba-favorites-count-row")

    assert mytba_favorites_row is not None
    assert mytba_favorites_row.text.strip() == "Favorites:\n{}".format(favorites_count)


def test_num_subscriptions(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    subscriptions_count = randint(1, 100)

    login_user.subscriptions_count = subscriptions_count

    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    mytba_subscriptions_row = soup.find(id="mytba-subscriptions-count-row")

    assert mytba_subscriptions_row is not None
    assert mytba_subscriptions_row.text.strip() == "Subscriptions:\n{}".format(
        subscriptions_count
    )


def test_submissions_pending(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    submissions_pending_count = randint(1, 100)

    login_user.submissions_pending_count = submissions_pending_count

    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    submissions_pending_row = soup.find(id="submissions-pending-count-row")

    assert submissions_pending_row is not None
    assert submissions_pending_row.text.strip() == "Pending:\n{}".format(
        submissions_pending_count
    )


def test_submissions_accepted(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    submissions_accepted_count = randint(1, 100)

    login_user.submissions_accepted_count = submissions_accepted_count

    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    submissions_accepted_row = soup.find(id="submissions-accepted-count-row")

    assert submissions_accepted_row is not None
    assert submissions_accepted_row.text.strip() == "Accepted:\n{}".format(
        submissions_accepted_count
    )


def test_submissions_reviewed(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    submissions_reviewed_count = randint(1, 100)

    login_user.submissions_reviewed_count = submissions_reviewed_count

    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    submissions_reviewed_row = soup.find(id="submissions-reviewed-count-row")

    assert submissions_reviewed_row is not None
    assert submissions_reviewed_row.text.strip() == "Reviewed:\n{}".format(
        submissions_reviewed_count
    )


@pytest.mark.parametrize("has_review_permissions", [(True), (False)])
def test_has_review_permissions(
    login_user,
    has_review_permissions: bool,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    login_user.has_review_permissions = has_review_permissions

    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    review_permissions_row = soup.find(id="review-permissions-row")

    if has_review_permissions:
        assert review_permissions_row
    else:
        assert review_permissions_row is None


@pytest.mark.parametrize("setup_keys", [(True), (False)])
def test_api_read_keys(
    login_user,
    setup_keys: bool,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    api_key_id = "some_api_key"
    api_key_created = datetime.datetime.now()
    api_key_description = "Testing API Read Key"

    api_read_key = Mock()
    api_read_key.created = api_key_created
    api_read_key.description = api_key_description
    api_read_key.key.configure_mock(**{"id.return_value": api_key_id})

    login_user.api_read_keys = [api_read_key] if setup_keys else []

    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    api_read = soup.find_all("tr", attrs={"class": "api-read-key"})

    if setup_keys:
        assert len(api_read) == 1
        api_read = api_read[0]
        assert [td.text.strip() for td in api_read.find_all("td")] == [
            "some_api_key",
            api_key_created.strftime("%Y-%m-%d"),
            api_key_description,
            "Delete",
        ]

        # Last TD should be a form with proper delete information
        delete_form = api_read.find("form")
        assert delete_form is not None
        assert delete_form.get("method") == "POST"
        assert delete_form.get("action") == "/account/api/read_key_delete"

        delete_form_input = delete_form.find_all("input")
        assert set([input.get("type") for input in delete_form_input]) == {"hidden"}
        assert [
            (input.get("name"), input.get("value")) for input in delete_form_input
        ] == [("key_id", "some_api_key"), ("csrf_token", ANY)]

        delete_form_button = delete_form.find(
            "button", attrs={"class": "btn btn-danger", "type": "submit"}
        )
        assert delete_form_button.text == " Delete"
    else:
        assert len(api_read) == 0


@pytest.mark.parametrize(
    "setup_keys, key_expires", [(True, False), (True, True), (False, False)]
)
def test_api_write_keys(
    login_user,
    setup_keys: bool,
    key_expires: bool,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    event = Mock()
    event_id = "event_id"
    event.configure_mock(**{"id.return_value": event_id})

    api_key_id = "some_api_key"
    api_key_secret = "some_api_key_secret"
    api_write_key_expiration = datetime.datetime.now()
    api_write_key = Mock(
        event_list=[event],
        auth_types_enum=[AuthType.MATCH_VIDEO, AuthType.ZEBRA_MOTIONWORKS],
    )
    if key_expires:
        api_write_key.expiration = api_write_key_expiration
    else:
        api_write_key.expiration = None
    api_write_key.secret = api_key_secret
    api_write_key.key.configure_mock(**{"id.return_value": api_key_id})

    login_user.api_write_keys = [api_write_key] if setup_keys else []

    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    api_write = soup.find_all("tr", attrs={"class": "api-write-key"})

    if setup_keys:
        assert len(api_write) == 1
        api_write = api_write[0]

        api_write_tds = api_write.find_all("td")

        # First TD is two links - one to the event + one to event wizard
        api_write_event_links = api_write_tds[0].find_all("a")
        assert [(link.get("href"), link.text) for link in api_write_event_links] == [
            ("/event/event_id", "event_id"),
            ("/eventwizard?event=event_id", "EventWizard"),
        ]

        # Second TD is a list of permissions for the key
        assert [li.text for li in api_write_tds[1].find_all("li")] == [
            "match video",
            "zebra motionworks",
        ]

        # Third TD is the expiration for the key
        if key_expires:
            assert api_write_tds[2].text.strip() == api_write_key_expiration.strftime(
                "%Y-%m-%d"
            )
        else:
            assert api_write_tds[2].text.strip() == "--"

        # Fourth TD is the key ID
        assert api_write_tds[3].text.strip() == api_key_id

        # Fifth TD is the key secret
        assert api_write_tds[4].text.strip() == api_key_secret
    else:
        assert len(api_write) == 0


def test_auth_write_type_names(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["auth_write_type_names"] == AUTH_TYPE_WRITE_TYPE_NAMES


def test_overview_api_read_add_form(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    api_read_key_form = soup.find("form", id="api-read-key-add")
    assert api_read_key_form is not None
    assert api_read_key_form.get("action") == "/account/api/read_key_add"
    assert api_read_key_form.get("method") == "POST"

    api_read_key_form_inputs = api_read_key_form.find_all("input")
    assert [
        (input.get("name"), input.get("value"), input.get("type"))
        for input in api_read_key_form_inputs
    ] == [("description", None, "text"), ("csrf_token", ANY, "hidden")]

    api_read_key_form_button = api_read_key_form.find(
        "button", attrs={"class": "btn btn-success", "type": "submit"}
    )
    assert api_read_key_form_button.text == " Add New Key"


def test_overview_api_write_add_button(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    assert template.name == "account_overview.html"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    api_write_key_row = soup.find(
        "div", attrs={"class": "row"}, id="api-write-keys-row"
    )
    api_write_key_row_button = api_write_key_row.find(
        "a", attrs={"href": "request/apiwrite", "class": "btn btn-success pull-right"}
    )
    assert api_write_key_row_button.text == " Request Tokens"
