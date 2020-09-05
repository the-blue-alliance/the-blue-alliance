from unittest.mock import Mock, patch
from urllib.parse import parse_qsl, urlparse

import pytest
import werkzeug
from flask import request
from google.cloud import ndb

import backend.web.auth as backend_auth
from backend.common.consts.account_permission import AccountPermission
from backend.common.models.account import Account
from backend.web.handlers.decorators import (
    require_admin,
    require_login,
    require_login_only,
    require_permission,
)


def test_require_login_only_no_user() -> None:
    from backend.web.main import app

    func = Mock()
    decorated_func = require_login_only(func)
    with app.test_request_context("/"):
        response = decorated_func(None, request)
    assert not func.called
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {"next": "http://localhost/"}


def test_require_login_only() -> None:
    from backend.web.main import app

    func = Mock()
    with patch.object(
        backend_auth, "_decoded_claims", return_value={"abc": "abc"}
    ), app.test_request_context("/"):
        decorated_func = require_login_only(func)
        decorated_func(None, request)
    func.assert_called_with(None, request)


def test_require_login_no_user() -> None:
    from backend.web.main import app

    func = Mock()
    decorated_func = require_login(func)
    with app.test_request_context("/"):
        response = decorated_func(request)
    assert not func.called
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {"next": "http://localhost/"}


def test_require_login_not_registered() -> None:
    from backend.web.main import app

    func = Mock()
    decorated_func = require_login(func)
    with patch.object(
        backend_auth, "_decoded_claims", return_value={"abc": "abc"}
    ), app.test_request_context("/"):
        response = decorated_func(request)
    assert not func.called
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/register"
    assert dict(parse_qsl(parsed_response.query)) == {"next": "http://localhost/"}


def test_require_login(ndb_client: ndb.Client) -> None:
    from backend.web.main import app

    with ndb_client.context():
        a = Account(email="zach@thebluealliance.com", registered=True)
        a.put()

        func = Mock()
        with patch.object(
            backend_auth,
            "_decoded_claims",
            return_value={"email": "zach@thebluealliance.com"},
        ), app.test_request_context("/"):
            decorated_func = require_login(func)
            decorated_func(request)
        func.assert_called_with(request)


def test_require_admin_no_user() -> None:
    from backend.web.main import app

    func = Mock()
    decorated_func = require_admin(func)
    with app.test_request_context("/"):
        response = decorated_func(None, request)
    assert not func.called
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {"next": "http://localhost/"}


def test_require_admin_not_registered(ndb_client: ndb.Client) -> None:
    from backend.web.main import app

    with ndb_client.context():
        func = Mock()
        decorated_func = require_admin(func)
        with patch.object(
            backend_auth,
            "_decoded_claims",
            return_value={"uid": "abc", "email": "zach@thebluealliance.com"},
        ), app.test_request_context("/"):
            with pytest.raises(werkzeug.exceptions.Unauthorized):
                decorated_func(None, request)
        assert not func.called


def test_require_admin(ndb_client: ndb.Client) -> None:
    from backend.web.main import app

    with ndb_client.context():
        func = Mock()
        with patch.object(
            backend_auth,
            "_decoded_claims",
            return_value={
                "uid": "abc",
                "email": "zach@thebluealliance.com",
                "admin": True,
            },
        ), app.test_request_context("/"):
            decorated_func = require_admin(func)
            decorated_func(None, request)
        func.assert_called_with(None, request)


def test_require_permission_user(ndb_client: ndb.Client) -> None:
    from backend.web.main import app

    func = Mock()
    decorated_func = require_permission(AccountPermission.REVIEW_MEDIA)(func)
    with app.test_request_context("/"):
        response = decorated_func(None, request)
    assert not func.called
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {"next": "http://localhost/"}


def test_require_permission_false(ndb_client: ndb.Client) -> None:
    from backend.web.main import app

    with ndb_client.context():
        a = Account(email="zach@thebluealliance.com", permissions=[])
        a.put()

        func = Mock()
        with patch.object(
            backend_auth,
            "_decoded_claims",
            return_value={"email": "zach@thebluealliance.com"},
        ), app.test_request_context("/"):
            with pytest.raises(werkzeug.exceptions.Unauthorized):
                decorated_func = require_permission(AccountPermission.REVIEW_MEDIA)(
                    func
                )
                decorated_func(None, request)
        assert not func.called


def test_require_permission(ndb_client: ndb.Client) -> None:
    from backend.web.main import app

    with ndb_client.context():
        a = Account(
            email="zach@thebluealliance.com",
            permissions=[AccountPermission.REVIEW_MEDIA],
        )
        a.put()

        func = Mock()
        with patch.object(
            backend_auth,
            "_decoded_claims",
            return_value={"email": "zach@thebluealliance.com"},
        ), app.test_request_context("/"):
            decorated_func = require_permission(AccountPermission.REVIEW_MEDIA)(func)
            decorated_func(None, request)
        func.assert_called_with(None, request)
