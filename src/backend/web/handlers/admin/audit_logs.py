from typing import List, Optional

from flask import request
from google.appengine.ext import ndb

from backend.common.models.account import Account
from backend.common.models.audit_log_entry import AuditLogEntry
from backend.web.profiled_render import render_template


def _parse_lookup_key(raw_key: str) -> Optional[ndb.Key]:
    lookup = raw_key.strip()
    if not lookup:
        return None

    try:
        return ndb.Key(urlsafe=lookup.encode("utf-8"))
    except Exception:
        pass

    kind, separator, id_part = lookup.partition(":")
    if not separator:
        return None
    if not kind or not id_part:
        return None

    if id_part.isdigit():
        return ndb.Key(kind, int(id_part))
    return ndb.Key(kind, id_part)


def audit_logs() -> str:
    lookup_key_raw = request.args.get("key", "").strip()
    target_key = _parse_lookup_key(lookup_key_raw) if lookup_key_raw else None

    error: Optional[str] = None
    logs: List[AuditLogEntry] = []
    accounts_by_key: dict[ndb.Key, Account] = {}

    if lookup_key_raw and target_key is None:
        error = "Unable to parse datastore key. Use urlsafe key or Kind:id format."
    elif target_key is not None:
        # Negation for descending order is valid NDB syntax, but Pyre doesn't understand it
        logs = (
            AuditLogEntry.query(AuditLogEntry.target_key == target_key)
            .order(-AuditLogEntry.time)  # pyre-ignore[16]
            .fetch(200)
        )
        account_keys = list({log.account for log in logs if log.account is not None})
        accounts = ndb.get_multi(account_keys)
        accounts_by_key = {
            account.key: account for account in accounts if account is not None
        }

    template_values = {
        "lookup_key_raw": lookup_key_raw,
        "target_key": target_key,
        "error": error,
        "logs": logs,
        "accounts_by_key": accounts_by_key,
    }
    return render_template("admin/audit_logs.html", template_values)
