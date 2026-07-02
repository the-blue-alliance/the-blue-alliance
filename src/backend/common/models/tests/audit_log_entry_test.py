from google.appengine.ext import ndb

from backend.common.models.account import Account
from backend.common.models.audit_log_entry import AuditLogEntry


def test_audit_log_entry_fields() -> None:
    account_key = Account(email="audit@thebluealliance.com").put()
    target_key = ndb.Key("Event", "2026casj")

    entry = AuditLogEntry(
        account=account_key,
        endpoint="webcast_mod.webcast_remove",
        target_key=target_key,
        url_args={"event_key": "2026casj"},
        form_params={"type": ["twitch"], "channel": ["frc0"]},
    )
    entry_key = entry.put()

    stored = entry_key.get()
    assert stored is not None
    assert stored.time is not None
    assert stored.account == account_key
    assert stored.endpoint == "webcast_mod.webcast_remove"
    assert stored.target_key == target_key
    assert stored.url_args == {"event_key": "2026casj"}
    assert stored.form_params == {"type": ["twitch"], "channel": ["frc0"]}
