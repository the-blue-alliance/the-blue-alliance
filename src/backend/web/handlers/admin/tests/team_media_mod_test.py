from datetime import datetime

from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.helpers.deferred import run_from_task
from backend.common.models.account import Account
from backend.common.models.team_admin_access import TeamAdminAccess


def test_add_team_media_mod_deferred(
    login_gae_admin,
    web_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = web_client.post(
        "/admin/media/modcodes/add",
        data={
            "year": 2023,
            "auth_codes_csv": "254,abc123\n255,def456",
        },
    )
    assert resp.status_code == 302

    for i in range(2):
        tasks = taskqueue_stub.get_filtered_tasks(queue_names="admin")
        for task in tasks:
            run_from_task(task)

    access1 = TeamAdminAccess.get_by_id("frc254_2023")
    assert access1 is not None
    assert access1.team_number == 254
    assert access1.year == 2023
    assert access1.access_code == "abc123"
    assert access1.expiration == datetime(2023, 7, 1)

    access2 = TeamAdminAccess.get_by_id("frc255_2023")
    assert access2 is not None
    assert access2.team_number == 255
    assert access2.year == 2023
    assert access2.access_code == "def456"
    assert access2.expiration == datetime(2023, 7, 1)


def test_add_team_media_mod_batched(
    login_gae_admin,
    web_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = web_client.post(
        "/admin/media/modcodes/add",
        data={
            "year": 2023,
            "auth_codes_csv": "\n".join([f"{i},abc123" for i in range(1, 10000)]),
        },
    )
    assert resp.status_code == 302

    for i in range(2):
        tasks = taskqueue_stub.get_filtered_tasks(queue_names="admin")
        for task in tasks:
            run_from_task(task)

    modcodes = TeamAdminAccess.query().fetch()
    assert len(modcodes) == 9999


def test_edit_team_media_mod_doest_exist(login_gae_admin, web_client: Client) -> None:
    resp = web_client.get("/admin/media/modcodes/edit/254/2023")
    assert resp.status_code == 404


def test_edit_team_media_mod(login_gae_admin, web_client: Client) -> None:
    account = Account(email="foo@bar.com")
    modcode = TeamAdminAccess(
        id="frc254_2023",
        team_number=254,
        year=2023,
        access_code="abc123",
        expiration=datetime(2023, 7, 1),
    )

    account_key = account.put()
    modcode.put()

    resp = web_client.get("/admin/media/modcodes/edit/254/2023")
    assert resp.status_code == 200

    new_access = "def456"
    new_expiration = "2023-08-01"
    new_email = "foo@bar.com"

    resp = web_client.post(
        "/admin/media/modcodes/edit/254/2023",
        data={
            "access_code": new_access,
            "expiration": new_expiration,
            "account_email": new_email,
        },
    )
    assert resp.status_code == 302

    access = TeamAdminAccess.get_by_id("frc254_2023")
    assert access is not None
    assert access.team_number == 254
    assert access.year == 2023
    assert access.access_code == "def456"
    assert access.expiration == datetime(2023, 8, 1)
    assert access.account == account_key
