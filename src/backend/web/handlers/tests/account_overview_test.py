from random import randint
from typing import List
from unittest.mock import Mock, patch
from urllib.parse import parse_qsl, urlparse

import bs4
import pytest
from flask import Flask
from werkzeug.test import Client

import backend
import backend.web.auth as backend_auth
from backend.common.consts.auth_type import (
    WRITE_TYPE_NAMES as AUTH_TYPE_WRITE_TYPE_NAMES,
)
from backend.common.sitevars.notifications_enable import NotificationsEnable
from backend.web.handlers.account import blueprint
from backend.web.handlers.tests.conftest import CapturedTemplate
from backend.web.handlers.tests.helpers import assert_alert, get_page_title


def user_mock(registered: bool = True) -> Mock:
    mock = Mock()
    mock.is_registered = registered
    mock.api_read_keys = []
    mock.api_write_keys = []
    mock.mobile_clients = []
    return mock


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
        "/account/register": "account.register",
        "/account/logout": "account.logout",
        "/account/login": "account.login",
        "/account/edit": "account.edit",
        "/account": "account.overview",
    }


def test_overview_logged_out(web_client: Client) -> None:
    response = web_client.get("/account")
    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account"
    }


def test_overview_unregistered(web_client: Client) -> None:
    mock = user_mock(registered=False)
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/register"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/account"
    }


def test_overview(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
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
        "num_favorites",
        "num_subscriptions",
        "submissions_pending",
        "submissions_accepted",
        "submissions_reviewed",
        "review_permissions",
        "api_read_keys",
        "api_write_keys",
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
    status: str,
    message: str,
    success: bool,
    captured_templates: List[CapturedTemplate],
    web_client: Client,
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account?status={}".format(status))

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
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
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
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    webhook_verification_success = "1"

    mock = user_mock()
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get(
            "/account?webhook_verification_success={}".format(
                webhook_verification_success
            )
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
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
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
    ping_sent: str,
    success: bool,
    captured_templates: List[CapturedTemplate],
    web_client: Client,
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account?ping_sent={}".format(ping_sent))

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
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
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
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    mock = user_mock()
    # Add a dummy client so we have something to ping, to check that the ping rows are disabled
    mock.mobile_clients = [Mock()]

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        backend_auth, "current_user", return_value=mock
    ), patch.object(
        NotificationsEnable, "notifications_enabled", return_value=True
    ):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["ping_enabled"] == ""

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    ping_button = soup.find("button", attrs={"class": "ping"})
    assert "disabled" not in list(ping_button.attrs)


def test_ping_disabled(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    mock = user_mock()
    # Add a dummy client so we have something to ping, to check that the ping rows are disabled
    mock.mobile_clients = [Mock()]

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        backend_auth, "current_user", return_value=mock
    ), patch.object(
        NotificationsEnable, "notifications_enabled", return_value=False
    ):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["ping_enabled"] == "disabled"

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    ping_button_disabled = soup.find("button", attrs={"class": "ping", "disabled": ""})
    assert ping_button_disabled


def test_num_favorites(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    favorites_count = randint(1, 100)

    mock = user_mock()
    mock.favorites_count = favorites_count

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(
        backend.web.handlers.account, "current_user", return_value=mock
    ), patch.object(
        backend_auth, "current_user", return_value=mock
    ):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["num_favorites"] == favorites_count


def test_num_subscriptions(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    subscriptions_count = randint(1, 100)

    mock = user_mock()
    mock.subscriptions_count = subscriptions_count

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["num_subscriptions"] == subscriptions_count


def test_submissions_pending(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    submissions_pending_count = randint(1, 100)

    mock = user_mock()
    mock.submissions_pending_count = submissions_pending_count

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["submissions_pending"] == submissions_pending_count


def test_submissions_accepted(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    submissions_accepted_count = randint(1, 100)

    mock = user_mock()
    mock.submissions_accepted_count = submissions_accepted_count

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["submissions_accepted"] == submissions_accepted_count


def test_submissions_reviewed(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    submissions_reviewed_count = randint(1, 100)

    mock = user_mock()
    mock.submissions_reviewed_count = submissions_reviewed_count

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["submissions_reviewed"] == submissions_reviewed_count


@pytest.mark.parametrize("has_review_permissions", [(True), (False)])
def test_has_review_permissions(
    has_review_permissions: bool,
    captured_templates: List[CapturedTemplate],
    web_client: Client,
) -> None:
    mock = user_mock()
    mock.has_review_permissions = has_review_permissions

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["review_permissions"] == has_review_permissions

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    review_permissions_row = soup.find(id="review-permissions-row")

    if has_review_permissions:
        assert review_permissions_row
    else:
        assert review_permissions_row is None


def test_api_read_keys(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    api_read_keys = [Mock()]

    mock = user_mock()
    mock.api_read_keys = api_read_keys

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["api_read_keys"] == api_read_keys


def test_api_write_keys(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    api_write_keys = [Mock(event_list=[], auth_types_enum=[])]

    mock = user_mock()
    mock.api_write_keys = api_write_keys

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["api_write_keys"] == api_write_keys


def test_auth_write_type_names(
    captured_templates: List[CapturedTemplate], web_client: Client,
) -> None:
    mock = user_mock()
    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock
    ), patch.object(backend.web.handlers.account, "current_user", return_value=mock):
        response = web_client.get("/account")

    assert response.status_code == 200
    assert len(captured_templates) == 1

    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "account_overview.html"
    assert context["auth_write_type_names"] == AUTH_TYPE_WRITE_TYPE_NAMES
