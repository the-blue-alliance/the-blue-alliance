from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.client_type import ClientType
from backend.common.helpers.deferred import run_from_task
from backend.common.models.account import Account
from backend.common.models.mobile_client import MobileClient
from backend.web.handlers.admin.mobile_clients import _dedupe_mobile_clients


def test_dashboard_requires_admin(web_client: Client) -> None:
    resp = web_client.get("/admin/mobile_clients")
    assert resp.status_code == 401


def test_dashboard_renders_stats(web_client: Client, login_gae_admin, ndb_stub) -> None:
    account_one = ndb.Key(Account, "user1")
    for uuid in ("uuid-a", "uuid-b"):
        MobileClient(
            parent=account_one,
            user_id="user1",
            messaging_id="token-shared",
            client_type=ClientType.OS_IOS,
            device_uuid=uuid,
            display_name="iPhone",
        ).put()
    MobileClient(
        parent=ndb.Key(Account, "user2"),
        user_id="user2",
        messaging_id="other-token",
        client_type=ClientType.OS_ANDROID_FCM,
        device_uuid="uuid-x",
        display_name="Pixel",
    ).put()

    resp = web_client.get("/admin/mobile_clients")
    assert resp.status_code == 200
    assert b"Total registered clients" in resp.data
    # 3 clients total
    assert b"<dd>3</dd>" in resp.data


def test_dedupe_post_enqueues_task(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    account_key = ndb.Key(Account, "user1")
    for uuid in ("uuid-a", "uuid-b", "uuid-c"):
        MobileClient(
            parent=account_key,
            user_id="user1",
            messaging_id="token-shared",
            client_type=ClientType.OS_IOS,
            device_uuid=uuid,
            display_name="iPhone",
        ).put()

    resp = web_client.post("/admin/mobile_clients/dedupe")
    assert resp.status_code == 302

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="admin")
    assert len(tasks) == 1
    run_from_task(tasks[0])

    rows = MobileClient.query(ancestor=account_key).fetch()
    assert len(rows) == 1
    assert rows[0].messaging_id == "token-shared"


def test_dedupe_collapses_per_account_groups(ndb_stub) -> None:
    account_one = ndb.Key(Account, "user1")
    account_two = ndb.Key(Account, "user2")

    # user1 has 3 rows for the same token (the duplicate case from prod).
    for uuid in ("uuid-a", "uuid-b", "uuid-c"):
        MobileClient(
            parent=account_one,
            user_id="user1",
            messaging_id="token-shared",
            client_type=ClientType.OS_IOS,
            device_uuid=uuid,
            display_name="iPhone",
        ).put()

    # user1 has another distinct token — should be untouched.
    MobileClient(
        parent=account_one,
        user_id="user1",
        messaging_id="token-other",
        client_type=ClientType.OS_IOS,
        device_uuid="uuid-other",
        display_name="iPad",
    ).put()

    # user2 happens to also have token-shared (cross-account) — different
    # account, so it should NOT be collapsed with user1's group.
    MobileClient(
        parent=account_two,
        user_id="user2",
        messaging_id="token-shared",
        client_type=ClientType.OS_IOS,
        device_uuid="uuid-x",
        display_name="iPhone",
    ).put()

    deleted = _dedupe_mobile_clients()
    assert deleted == 2

    rows_one = MobileClient.query(ancestor=account_one).fetch()
    rows_two = MobileClient.query(ancestor=account_two).fetch()
    assert len(rows_one) == 2
    assert sorted(c.messaging_id for c in rows_one) == ["token-other", "token-shared"]
    assert len(rows_two) == 1


def test_dedupe_skips_webhooks(ndb_stub) -> None:
    """Webhooks share the MobileClient kind but are managed separately by the
    user-facing webhooks UI. The admin dedupe must never touch them, even when
    multiple webhook rows under the same account share a `messaging_id` (URL)."""
    account_key = ndb.Key(Account, "user1")

    # Two webhook rows that look duplicated to the dedupe logic — these should
    # be left alone.
    for verification_code in ("code-a", "code-b"):
        MobileClient(
            parent=account_key,
            user_id="user1",
            messaging_id="https://example.com/webhook",
            client_type=ClientType.WEBHOOK,
            device_uuid="",
            display_name="My Webhook",
            verification_code=verification_code,
        ).put()

    # And actual mobile-client dupes that SHOULD be collapsed.
    for uuid in ("uuid-a", "uuid-b"):
        MobileClient(
            parent=account_key,
            user_id="user1",
            messaging_id="token-shared",
            client_type=ClientType.OS_IOS,
            device_uuid=uuid,
            display_name="iPhone",
        ).put()

    deleted = _dedupe_mobile_clients()
    assert deleted == 1

    rows = MobileClient.query(ancestor=account_key).fetch()
    webhook_rows = [r for r in rows if r.client_type == ClientType.WEBHOOK]
    ios_rows = [r for r in rows if r.client_type == ClientType.OS_IOS]
    assert len(webhook_rows) == 2
    assert len(ios_rows) == 1


def test_dedupe_paginates(ndb_stub, taskqueue_stub) -> None:
    """With more rows than page_size, dedupe self-defers and the deferred
    tasks complete the scan. Idempotent: groups whose rows straddle page
    boundaries are still fully collapsed because each group is fetched via
    ancestor query, not in-batch grouping."""
    account_one = ndb.Key(Account, "user1")
    account_two = ndb.Key(Account, "user2")

    for uuid in ("uuid-a", "uuid-b", "uuid-c"):
        MobileClient(
            parent=account_one,
            user_id="user1",
            messaging_id="token-a",
            client_type=ClientType.OS_IOS,
            device_uuid=uuid,
            display_name="iPhone",
        ).put()
    for uuid in ("uuid-d", "uuid-e"):
        MobileClient(
            parent=account_two,
            user_id="user2",
            messaging_id="token-b",
            client_type=ClientType.OS_IOS,
            device_uuid=uuid,
            display_name="iPhone",
        ).put()

    # page_size=2 forces multiple pages across the 5-row dataset.
    _dedupe_mobile_clients(page_size=2)

    # Drain any self-deferred follow-up pages.
    while True:
        tasks = taskqueue_stub.get_filtered_tasks(queue_names="admin")
        if not tasks:
            break
        for task in tasks:
            run_from_task(task)
        taskqueue_stub.FlushQueue("admin")

    rows_one = MobileClient.query(ancestor=account_one).fetch()
    rows_two = MobileClient.query(ancestor=account_two).fetch()
    assert len(rows_one) == 1
    assert rows_one[0].messaging_id == "token-a"
    assert len(rows_two) == 1
    assert rows_two[0].messaging_id == "token-b"
