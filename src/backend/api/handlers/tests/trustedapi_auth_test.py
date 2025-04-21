import datetime
import json
import random
import string
from typing import List, Optional, Tuple
from unittest.mock import Mock

from freezegun import freeze_time
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from pytest import MonkeyPatch
from werkzeug.test import Client

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common import auth
from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.keys import EventKey


def setup_event(
    event_type: EventType = EventType.OFFSEASON,
    official: bool = False,
) -> None:
    Event(
        id="2019nyny",
        year=2019,
        event_short="nyny",
        event_type_enum=event_type,
        official=official,
    ).put()


def setup_cmp_event() -> None:
    Event(
        id="2019cur",
        year=2019,
        event_short="cur",
        event_type_enum=EventType.CMP_DIVISION,
        official=True,
    ).put()


def setup_user(
    monkeypatch: MonkeyPatch,
    permissions: List[AccountPermission] = [],
    is_admin: bool = False,
) -> ndb.Key:
    email = "zach@thebluealliance.com"
    account = Account(
        email=email,
        permissions=permissions,
    )
    account.put()

    monkeypatch.setattr(
        auth, "_decoded_claims", Mock(return_value={"email": email, "admin": is_admin})
    )
    return account.key


def setup_api_auth(
    event_key: Optional[EventKey],
    auth_types: List[AuthType] = [],
    expiration: Optional[datetime.datetime] = None,
    owner: Optional[ndb.Key] = None,
    all_official_events: bool = False,
) -> Tuple[str, str]:
    auth = ApiAuthAccess(
        id="".join(random.choices(string.ascii_letters + string.digits, k=10)),
        secret="".join(random.choices(string.ascii_letters + string.digits, k=10)),
        event_list=[ndb.Key(Event, event_key)] if event_key else [],
        auth_types_enum=auth_types,
        expiration=expiration,
        owner=owner,
        all_official_events=all_official_events,
    )
    auth.put()

    return none_throws(auth.key.string_id()), none_throws(auth.secret)


def test_no_event(ndb_stub, api_client: Client) -> None:
    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post("/api/trusted/v1/event/2019nyny/team_list/update")

    assert resp.status_code == 404
    assert resp.json["Error"] == "Event 2019nyny not found"


def test_not_authenticated(ndb_stub, api_client: Client) -> None:
    setup_event()

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post("/api/trusted/v1/event/2019nyny/team_list/update")

    assert resp.status_code == 401
    assert (
        resp.json["Error"] == "Must provide a request header parameter 'X-TBA-Auth-Id'"
    )


def test_has_auth_id_but_no_sig(ndb_stub, api_client: Client) -> None:
    setup_event()

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post(
            "/api/trusted/v1/event/2019nyny/team_list/update",
            headers={"X-TBA-Auth-Id": "auth_id"},
        )

    assert resp.status_code == 401
    assert (
        resp.json["Error"] == "Must provide a request header parameter 'X-TBA-Auth-Sig'"
    )


@freeze_time("2020-06-01")
def test_admin_superpower(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    Admins can use the trusted API on anything, even official events in the past
    """
    setup_event(event_type=EventType.REGIONAL)
    setup_user(monkeypatch, is_admin=True)

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post(
            "/api/trusted/v1/event/2019nyny/team_list/update",
            data=json.dumps([]),
        )

    assert resp.status_code == 200
    assert "Success" in resp.json


@freeze_time("2019-06-01")
def test_eventwizard_permission_not_offseason(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    Users with the EventWizard account permission can only use it for current-year offseason events
    Here, making a request for an official event in the current year should fail
    """
    setup_event(event_type=EventType.REGIONAL)
    setup_user(monkeypatch, permissions=[AccountPermission.OFFSEASON_EVENTWIZARD])

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post("/api/trusted/v1/event/2019nyny/team_list/update")

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2020-06-01")
def test_eventwizard_permission_not_this_year(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    Users with the EventWizard account permission can only use it for current-year offseason events
    Here, making a request for an offseason event in the past should fail
    """
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[AccountPermission.OFFSEASON_EVENTWIZARD])

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post("/api/trusted/v1/event/2019nyny/team_list/update")

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_eventwizard_permission_passes(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    Users with the EventWizard account permission can only use it for current-year offseason events
    Here, making a request for an offseason event in the current year should succeed
    """
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[AccountPermission.OFFSEASON_EVENTWIZARD])

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post(
            "/api/trusted/v1/event/2019nyny/team_list/update", data=json.dumps([])
        )

    assert resp.status_code == 200
    assert "Success" in resp.json


@freeze_time("2019-06-01")
def test_account_permission_logged_in_wrong_events(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect failure if the user's linked auth points to a different event
    """
    setup_event(event_type=EventType.OFFSEASON)
    account_key = setup_user(monkeypatch, permissions=[])
    setup_api_auth("2019other", auth_types=[AuthType.EVENT_TEAMS], owner=account_key)

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post("/api/trusted/v1/event/2019nyny/team_list/update")

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_account_permission_logged_in_wrong_permissions(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect failure if the linked auth points to the right event, but has the wrong permissions
    """
    setup_event(event_type=EventType.OFFSEASON)
    account_key = setup_user(monkeypatch, permissions=[])
    setup_api_auth("2019nyny", auth_types=[AuthType.EVENT_RANKINGS], owner=account_key)

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post("/api/trusted/v1/event/2019nyny/team_list/update")

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_account_permission_logged_in_auth_expired(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect failure if the linked auth is valid, but expired
    """
    setup_event(event_type=EventType.OFFSEASON)
    account_key = setup_user(monkeypatch, permissions=[])
    setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        owner=account_key,
        expiration=datetime.datetime(2019, 1, 1),
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post("/api/trusted/v1/event/2019nyny/team_list/update")

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_account_permission_logged_in_good_forever(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect success for a linked auth that never expires
    """
    setup_event(event_type=EventType.OFFSEASON)
    account_key = setup_user(monkeypatch, permissions=[])
    setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        owner=account_key,
        expiration=None,
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post(
            "/api/trusted/v1/event/2019nyny/team_list/update", data=json.dumps([])
        )

    assert resp.status_code == 200
    assert "Success" in resp.json


@freeze_time("2019-06-01")
def test_account_permission_logged_in_not_expired_yet(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect success for a linked auth that has an expiration which has not yet occurred
    """
    setup_event(event_type=EventType.OFFSEASON)
    account_key = setup_user(monkeypatch, permissions=[])
    setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        owner=account_key,
        expiration=datetime.datetime(2019, 7, 1),
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        resp = api_client.post(
            "/api/trusted/v1/event/2019nyny/team_list/update", data=json.dumps([])
        )

    assert resp.status_code == 200
    assert "Success" in resp.json


@freeze_time("2019-06-01")
def test_explicit_auth_bad_id(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect failure if we pass an auth_id that doesn't exist in the db
    """
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth("2019nyny", auth_types=[AuthType.EVENT_TEAMS])

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019nyny/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": "wrong_" + auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_explicit_auth_bad_secret(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect failure if we pass a correct auth_id, but incorrect signature
    """
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth("2019nyny", auth_types=[AuthType.EVENT_TEAMS])

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019nyny/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": "wrong_"
                + TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_explicit_auth_wrong_event(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect failure if we pass a correct auth_id, but it is linked to the wrong event
    """
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019other", auth_types=[AuthType.EVENT_TEAMS]
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019nyny/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_explicit_auth_wrong_permission(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect failure if we pass a correct auth_id, but it does not have the right permissions
    """
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny", auth_types=[AuthType.EVENT_RANKINGS]
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019nyny/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_explicit_auth_expired(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect failure if we pass a valid auth_id, but it is expired
    """
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=datetime.datetime(2019, 1, 1),
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019nyny/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 401
    assert "Error" in resp.json


@freeze_time("2019-06-01")
def test_explicit_auth_good_forever(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect success if we pass a valid auth_id and it should never expire
    """
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019nyny/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 200, resp.data
    assert "Success" in resp.json


@freeze_time("2019-06-01")
def test_explicit_auth_not_expired(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we expect success if we pass a valid auth_id that has an expiration which has not yet occurred
    """
    setup_event(event_type=EventType.OFFSEASON)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        "2019nyny",
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=datetime.datetime(2019, 7, 1),
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019nyny/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 200, resp.data
    assert "Success" in resp.json


@freeze_time("2019-06-01")
def test_explicit_auth_all_official_events(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we can allow all "official" events to pass the key, a technique we use with FIRST HQ
    """
    setup_event(event_type=EventType.OFFSEASON, official=True)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        None,
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
        all_official_events=True,
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019nyny/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 200, resp.data
    assert "Success" in resp.json


@freeze_time("2019-06-01")
def test_explicit_auth_with_event_code_override(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    Ensure we can support requests being made with full CMP division names
    and resolve them to the correct events
    """
    setup_cmp_event()
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        None,
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
        all_official_events=True,
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019curie/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 200, resp.data
    assert "Success" in resp.json


@freeze_time("2020-06-01")
def test_explicit_auth_all_official_events_not_current_year_fails(
    monkeypatch: MonkeyPatch, ndb_stub, api_client: Client
) -> None:
    """
    If a user is logged in, we can automatically pull their linked auth, provided it is unexpired
    Here, we can allow all "official" events to pass the key, a technique we use with FIRST HQ
    """
    setup_event(event_type=EventType.OFFSEASON, official=True)
    setup_user(monkeypatch, permissions=[])
    auth_id, auth_secret = setup_api_auth(
        None,
        auth_types=[AuthType.EVENT_TEAMS],
        expiration=None,
        all_official_events=True,
    )

    with api_client.application.test_request_context():  # pyre-ignore[16]
        request_data = json.dumps([])
        request_path = "/api/trusted/v1/event/2019nyny/team_list/update"
        resp = api_client.post(
            request_path,
            headers={
                "X-TBA-Auth-Id": auth_id,
                "X-TBA-Auth-Sig": TrustedApiAuthHelper.compute_auth_signature(
                    auth_secret, request_path, request_data
                ),
            },
            data=request_data,
        )

    assert resp.status_code == 401, resp.data
    assert "Error" in resp.json
