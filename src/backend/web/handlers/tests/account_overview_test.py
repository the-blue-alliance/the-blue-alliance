import datetime
from random import randint
from typing import Any, List, Optional, Tuple
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
from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.sitevars.notifications_enable import NotificationsEnable
from backend.web.handlers.account import ACCOUNT_WRITE_TYPE_LABELS, blueprint
from backend.web.handlers.conftest import CapturedTemplate
from backend.web.handlers.tests.helpers import get_page_title


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


def _assert_alert(div: Any, message: str, success: bool) -> None:
    assert ("alert-success" if success else "alert-danger") in div["class"]
    assert div.find("button", attrs={"data-dismiss": "alert"})
    assert div.find(class_="account-alert-message").text == message


def _secret(td: Any) -> str:
    return td.find(class_="account-secret-value").text.strip()


def _stat(row: Any) -> Tuple[str, str]:
    return (row.find("th").text.strip(), row.find("td").text.strip())


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
        "auth_write_type_labels",
        "user",
    }
    assert set(context_keys) <= set(context)


@pytest.mark.parametrize(
    "status, message, success",
    [
        ("account_edit_success", "Profile updated.", True),
        ("read_key_add_success", "New read API key added.", True),
        (
            "read_key_add_no_description",
            "Add a description to create a read API key.",
            False,
        ),
        (
            "read_key_add_failure",
            "Couldn't add a read API key. If this keeps happening, please contact us.",
            False,
        ),
        ("read_key_delete_success", "Read API key deleted.", True),
        (
            "read_key_delete_failure",
            "Couldn't delete that read API key. If this keeps happening, please contact us.",
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
    _assert_alert(status, message, success)


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
    _assert_alert(webhook_alert, "Webhook verified.", True)


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
    _assert_alert(
        ping_alert, ("Ping sent." if success else "Couldn't send the ping."), success
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
    assert "turned off" in ping_button_disabled.find_parent("form")["title"]


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
    assert _stat(mytba_favorites_row) == ("Favorites", str(favorites_count))


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
    assert _stat(mytba_subscriptions_row) == ("Subscriptions", str(subscriptions_count))


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
    assert _stat(submissions_pending_row) == ("Pending", str(submissions_pending_count))


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
    assert _stat(submissions_accepted_row) == (
        "Accepted",
        str(submissions_accepted_count),
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
    assert _stat(submissions_reviewed_row) == (
        "Reviewed",
        str(submissions_reviewed_count),
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
        # The review UI moved to the PWA; the Jinja page no longer exists
        link = review_permissions_row.find(id="review-pending-suggestions-link")
        assert link["href"] == "https://beta.thebluealliance.com/suggest/review"
    else:
        assert review_permissions_row is None
        assert soup.find(id="submissions-reviewed-count-row") is None
        assert soup.find("a", href="/add-data").text.strip() == "How to add data →"


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
        tds = api_read.find_all("td")
        assert [tds[0].text.strip(), _secret(tds[1]), tds[2].text.strip()] == [
            api_key_description,
            "some_api_key",
            api_key_created.strftime("%Y-%m-%d"),
        ]
        # Read keys aren't masked, only copyable.
        assert "is-masked" not in tds[1].find(class_="account-secret-field")["class"]

        # Last TD should be a form with proper delete information
        delete_form = api_read.find("form")
        assert delete_form is not None
        assert delete_form.get("method") == "POST"
        assert delete_form.get("action") == "/account/api/read_key_delete"
        assert delete_form.get("data-confirm") == (
            "Delete the \u201cTesting API Read Key\u201d key? Apps using it will stop working."
        )

        delete_form_input = delete_form.find_all("input")
        assert set([input.get("type") for input in delete_form_input]) == {"hidden"}
        assert [
            (input.get("name"), input.get("value")) for input in delete_form_input
        ] == [("key_id", "some_api_key"), ("csrf_token", ANY)]

        delete_form_button = delete_form.find("button", attrs={"type": "submit"})
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
    api_write_key_expiration = datetime.datetime.now() + datetime.timedelta(days=30)
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
            "Match videos",
            "Zebra MotionWorks",
        ]

        # Third TD is the expiration for the key
        if key_expires:
            assert api_write_tds[2].text.strip() == api_write_key_expiration.strftime(
                "%Y-%m-%d"
            )
        else:
            assert api_write_tds[2].text.strip() == "Never"

        # Fourth TD is the key ID
        assert api_write_tds[3].text.strip() == api_key_id

        # Fifth TD is the key secret
        assert _secret(api_write_tds[4]) == api_key_secret
        assert (
            "is-masked" in api_write_tds[4].find(class_="account-secret-field")["class"]
        )
    else:
        assert len(api_write) == 0


@pytest.mark.parametrize(
    "path, expected_key_ids, expected_next_href, expected_caret",
    [
        # Default: newest events first, plain header (no caret until the user sorts).
        (
            "/account",
            ["key-2026", "key-2025", "key-multiple-events", "key-no-event"],
            "/account?api_write_keys_sort=asc",
            None,
        ),
        # An invalid value falls back to the default, still with no caret.
        (
            "/account?api_write_keys_sort=sideways",
            ["key-2026", "key-2025", "key-multiple-events", "key-no-event"],
            "/account?api_write_keys_sort=asc",
            None,
        ),
        # Explicit ascending: oldest first, caret points up, next click flips it.
        (
            "/account?api_write_keys_sort=asc",
            ["key-multiple-events", "key-2025", "key-2026", "key-no-event"],
            "/account?api_write_keys_sort=desc",
            "glyphicon-triangle-top",
        ),
        # Explicit descending: same order as the default, but the caret shows.
        (
            "/account?api_write_keys_sort=desc",
            ["key-2026", "key-2025", "key-multiple-events", "key-no-event"],
            "/account?api_write_keys_sort=asc",
            "glyphicon-triangle-bottom",
        ),
    ],
)
def test_api_write_keys_sorted_by_event_key(
    login_user,
    web_client: FlaskClient,
    path: str,
    expected_key_ids: List[str],
    expected_next_href: str,
    expected_caret: Optional[str],
) -> None:
    def api_write_key(key_id: str, event_ids: List[str]) -> Mock:
        events = []
        for event_id in event_ids:
            event = Mock()
            event.configure_mock(**{"id.return_value": event_id})
            events.append(event)

        key = Mock(event_list=events, auth_types_enum=[])
        key.expiration = None
        key.secret = "secret"
        key.key.configure_mock(**{"id.return_value": key_id})
        return key

    login_user.api_write_keys = [
        api_write_key("key-2026", ["2026nmrc"]),
        api_write_key("key-no-event", []),
        api_write_key("key-multiple-events", ["2025mrcmp", "2024nmrc"]),
        api_write_key("key-2025", ["2025nmrc"]),
    ]

    response = web_client.get(path)

    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")
    api_write_rows = soup.find_all("tr", attrs={"class": "api-write-key"})
    assert [
        row.find_all("td")[3].text.strip() for row in api_write_rows
    ] == expected_key_ids

    # The "Event" header is the control: one link that flips the direction.
    header_link = soup.find(id="api-write-keys-sort")
    assert header_link is not None
    assert header_link.get("href") == expected_next_href
    assert header_link.text.strip().startswith("Event")

    # Keys without an event always trail the list, whatever the direction.
    assert expected_key_ids[-1] == "key-no-event"

    # The caret only appears once the user has actively sorted, and it points
    # in the direction of the current order.
    carets = header_link.find_all("span", class_="glyphicon")
    if expected_caret is None:
        assert carets == []
    else:
        assert len(carets) == 1
        assert expected_caret in carets[0].get("class")


def test_auth_write_type_labels(
    login_user,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    context = captured_templates[0][1]
    assert context["auth_write_type_labels"] == ACCOUNT_WRITE_TYPE_LABELS


def test_account_write_type_labels_cover_every_write_type() -> None:
    assert set(ACCOUNT_WRITE_TYPE_LABELS) == set(AUTH_TYPE_WRITE_TYPE_NAMES)


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
        "button", attrs={"type": "submit"}
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
    api_write_key_row = soup.find("div", id="api-write-keys-row")
    api_write_key_row_button = api_write_key_row.find(
        "a", attrs={"href": "/request/apiwrite"}
    )
    assert api_write_key_row_button.text == " Request a Write Key"


def test_overview_empty_sections(login_user, web_client: FlaskClient) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")
    assert soup.find(id="api-read-keys") is None
    assert soup.find(id="api-write-keys") is None
    empty = [div.text.strip() for div in soup.find_all("div", class_="account-empty")]
    assert empty == [
        "You don't have any read API keys yet.",
        "You don't have any write API keys.",
        "No devices found.",
    ]


def test_api_write_keys_show_event_names(login_user, web_client: FlaskClient) -> None:
    Event(
        id="2026nhdur",
        year=2026,
        event_short="nhdur",
        event_type_enum=EventType.DISTRICT,
        name="NE District UNH Event",
        short_name="UNH",
    ).put()

    def event_key(key_id: str) -> Mock:
        event = Mock()
        event.configure_mock(**{"id.return_value": key_id})
        return event

    api_write_key = Mock(
        event_list=[event_key("2026nhdur"), event_key("2026zzzz")],
        auth_types_enum=[],
    )
    api_write_key.expiration = None
    api_write_key.secret = "secret"
    api_write_key.key.configure_mock(**{"id.return_value": "key"})
    login_user.api_write_keys = [api_write_key]

    response = web_client.get("/account")

    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")
    events = soup.find("tr", class_="api-write-key").find_all(
        "div", class_="account-write-key-event"
    )
    # Known events show year + display name with the key beneath; unknown ones fall back to the key.
    assert [e.find("a").text for e in events] == ["2026 UNH", "2026zzzz"]
    assert [e.find("a").get("href") for e in events] == [
        "/event/2026nhdur",
        "/event/2026zzzz",
    ]
    assert events[0].find(class_="account-event-key").text == "2026nhdur"
    assert events[1].find(class_="account-event-key") is None


def test_delete_account_is_last_section(login_user, web_client: FlaskClient) -> None:
    response = web_client.get("/account")

    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")
    delete_links = soup.find_all("a", href="/account/delete")
    assert len(delete_links) == 1
    section = delete_links[0].find_parent(id="delete-account-row")
    assert section is not None
    assert section.find_next_sibling() is None


@pytest.mark.parametrize(
    "verified, status, has_verify_link",
    [(True, "Verified", False), (False, "Not verified", True)],
)
def test_webhook_verification_status(
    login_user,
    web_client: FlaskClient,
    verified: bool,
    status: str,
    has_verify_link: bool,
) -> None:
    webhook = Mock(is_webhook=True, verified=verified, display_name="Scouting")
    webhook.key.configure_mock(**{"id.return_value": "wh1"})
    login_user.mobile_clients = [webhook]

    response = web_client.get("/account")

    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")
    assert soup.find(class_="account-webhook-status").text.strip() == status
    assert (soup.find("a", href="/webhooks/verify/wh1") is not None) == has_verify_link


def test_api_write_key_expired(login_user, web_client: FlaskClient) -> None:
    def api_write_key(key_id: str, days: int) -> Mock:
        key = Mock(event_list=[], auth_types_enum=[])
        key.expiration = datetime.datetime.now() + datetime.timedelta(days=days)
        key.secret = "secret"
        key.key.configure_mock(**{"id.return_value": key_id})
        return key

    login_user.api_write_keys = [api_write_key("live", 5), api_write_key("old", -5)]

    response = web_client.get("/account")

    assert response.status_code == 200
    soup = bs4.BeautifulSoup(response.data, "html.parser")
    rows = {
        row.find_all("td")[3].text.strip(): row
        for row in soup.find_all("tr", class_="api-write-key")
    }
    assert "account-key-expired" not in rows["live"]["class"]
    assert "Expired" not in rows["live"].find_all("td")[2].text
    assert "account-key-expired" in rows["old"]["class"]
    assert "Expired" in rows["old"].find_all("td")[2].text


def test_read_key_description_required(login_user, web_client: FlaskClient) -> None:
    response = web_client.get("/account")

    soup = bs4.BeautifulSoup(response.data, "html.parser")
    assert soup.find("input", id="form-description").has_attr("required")
