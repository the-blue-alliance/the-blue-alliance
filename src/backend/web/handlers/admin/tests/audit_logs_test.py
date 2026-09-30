from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.web.handlers.admin.audit_logs import _parse_lookup_key


def test_parse_lookup_key_blank() -> None:
    assert _parse_lookup_key("   ") is None


def test_parse_lookup_key_urlsafe(ndb_stub) -> None:
    key = ndb.Key("Team", "frc254")
    assert _parse_lookup_key(key.urlsafe().decode()) == key


def test_parse_lookup_key_no_separator() -> None:
    assert _parse_lookup_key("notakey") is None


def test_parse_lookup_key_missing_kind_or_id() -> None:
    assert _parse_lookup_key(":frc254") is None
    assert _parse_lookup_key("Team:") is None


def test_parse_lookup_key_integer_id() -> None:
    assert _parse_lookup_key("Account:123") == ndb.Key("Account", 123)


def test_audit_logs_unparseable_key(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/audit_logs?key=notakey")
    assert resp.status_code == 200
    assert b"Unable to parse datastore key" in resp.data
