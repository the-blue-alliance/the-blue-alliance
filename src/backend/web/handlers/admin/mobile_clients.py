import logging
from typing import Any

from flask import flash, redirect, url_for
from google.appengine.ext import ndb
from werkzeug import Response

from backend.common.consts.client_type import ClientType, NAMES as CLIENT_TYPE_NAMES
from backend.common.helpers.deferred import defer_safe
from backend.common.models.mobile_client import MobileClient
from backend.web.profiled_render import render_template

DEDUPE_PAGE_SIZE = 500


def mobile_clients_dashboard() -> str:
    type_counts = [
        (
            CLIENT_TYPE_NAMES[client_type],
            MobileClient.query(MobileClient.client_type == client_type).count(),
        )
        for client_type in ClientType
    ]
    template_values = {
        "type_counts": type_counts,
        "total_clients": sum(count for _, count in type_counts),
    }
    return render_template("admin/mobile_clients.html", template_values)


def mobile_clients_dedupe_post() -> Response:
    defer_safe(
        _dedupe_mobile_clients,
        _queue="admin",
        _target="py3-tasks-io",
    )
    flash(
        "Enqueued MobileClient dedupe task. Pages self-defer; "
        "watch logs for per-page deletion counts."
    )
    return redirect(url_for("admin.mobile_clients_dashboard"))


def _dedupe_mobile_clients(
    cursor_urlsafe: str | None = None,
    page_size: int = DEDUPE_PAGE_SIZE,
    total_deleted: int = 0,
) -> int:
    """
    Paginated scan over MobileClient: for each (account, messaging_id) group
    encountered in the page, keep the most recently `updated` row and delete
    the rest. The full group is fetched per ancestor query, so correctness
    holds when a group's rows straddle page boundaries; subsequent pages
    re-encountering the (already collapsed) group are idempotent no-ops.

    Webhooks (`client_type == ClientType.WEBHOOK`) are excluded — they share the
    MobileClient kind but are managed separately by the user-facing webhooks UI
    and must not be touched by this admin sweep.

    Self-defers the next page until the scan completes. Returns the running
    deletion total (the cumulative total is logged on completion).
    """
    # pyre-ignore[16]: pyre stubs don't list ndb.Cursor, but it exists at runtime
    cursor = ndb.Cursor(urlsafe=cursor_urlsafe) if cursor_urlsafe else None
    page, next_cursor, more = MobileClient.query().fetch_page(
        page_size, start_cursor=cursor
    )

    # Webhooks are filtered in Python rather than via a `!=` query filter:
    # NDB inequality filters become multi-queries and multi-queries with cursors
    # require explicit `__key__` ordering, which complicates pagination.
    seen_groups: set[tuple[Any, str]] = set()
    deleted = 0
    for client in page:
        if client.client_type == ClientType.WEBHOOK:
            continue
        group_key = (client.key.parent(), client.messaging_id)
        if group_key in seen_groups:
            continue
        seen_groups.add(group_key)

        rows = [
            r
            for r in MobileClient.query(
                MobileClient.messaging_id == client.messaging_id,
                ancestor=client.key.parent(),
            ).fetch()
            if r.client_type != ClientType.WEBHOOK
        ]
        if len(rows) <= 1:
            continue
        rows.sort(key=lambda c: c.updated, reverse=True)
        keys_to_delete = [r.key for r in rows[1:]]
        ndb.delete_multi(keys_to_delete)
        deleted += len(keys_to_delete)

    total_deleted += deleted
    logging.info(
        f"MobileClient dedupe page: deleted {deleted} "
        f"(running total: {total_deleted})"
    )

    if more and next_cursor is not None:
        defer_safe(
            _dedupe_mobile_clients,
            cursor_urlsafe=next_cursor.urlsafe(),
            page_size=page_size,
            total_deleted=total_deleted,
            _queue="admin",
            _target="py3-tasks-io",
        )
    else:
        logging.info(f"MobileClient dedupe complete: {total_deleted} deleted")
    return total_deleted
