from typing import List

import bs4
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.models.account import Account


def create_accounts(n: int, permissions: List[AccountPermission] = []) -> List[ndb.Key]:
    accounts = []
    for i in range(n):
        accounts.append(
            Account(
                id=f"account_{i}",
                email=f"test_{i}@thebluealliance.com",
                nickname=f"Test {i}",
                registered=True,
                permissions=permissions,
            )
        )
    return ndb.put_multi(accounts)


def test_user_list(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/users")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    page_selector = soup.find(id="page-selector")
    assert page_selector is not None

    selected_page = page_selector.find(class_="active")
    assert selected_page is not None
    assert selected_page.string == "1"


def test_user_list_explicit_page(web_client: Client, login_gae_admin) -> None:
    create_accounts(n=1005)
    resp = web_client.get("/admin/users/1")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")

    user_count = soup.find("h1")
    assert user_count.string == "1005 Users"

    page_selector = soup.find(id="page-selector")
    assert page_selector is not None

    selected_page = page_selector.find(class_="active")
    assert selected_page is not None
    assert selected_page.string == "2"


def test_user_list_page_out_of_range(web_client: Client, login_gae_admin) -> None:
    create_accounts(n=1005)
    resp = web_client.get("/admin/users/3")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")

    user_count = soup.find("h1")
    assert user_count.string == "1005 Users"

    page_selector = soup.find(id="page-selector")
    assert page_selector is not None

    selected_page = page_selector.find(class_="active")
    assert selected_page is not None
    assert selected_page.string == "1"


def test_user_detail(web_client: Client, login_gae_admin) -> None:
    account_key = create_accounts(n=1)[0]
    resp = web_client.get(f"/admin/user/{account_key.id()}")
    assert resp.status_code == 200


def test_user_detail_doesnt_exist(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/user/asdf")
    assert resp.status_code == 404


def test_user_edit(web_client: Client, login_gae_admin) -> None:
    account_key = create_accounts(n=1)[0]
    resp = web_client.get(f"/admin/user/edit/{account_key.id()}")
    assert resp.status_code == 200


def test_user_edit_doesnt_exist(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/user/edit/asdf")
    assert resp.status_code == 404


def test_user_edit_post(web_client: Client, login_gae_admin) -> None:
    account_key = create_accounts(n=1)[0]
    resp = web_client.post(
        f"/admin/user/edit/{account_key.id()}",
        data={
            "display_name": "Edited User",
            f"perm-{AccountPermission.REVIEW_MEDIA.value}": "checked",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == f"/admin/user/{account_key.id()}"

    account = account_key.get()
    assert account is not None
    assert account.display_name == "Edited User"
    assert account.permissions == [AccountPermission.REVIEW_MEDIA]


def test_user_edit_remove_permission(web_client: Client, login_gae_admin) -> None:
    account_key = create_accounts(n=1, permissions=[AccountPermission.REVIEW_MEDIA])[0]
    resp = web_client.post(
        f"/admin/user/edit/{account_key.id()}",
        data={
            "display_name": "Edited User",
            f"perm-{AccountPermission.REVIEW_EVENT_MEDIA.value}": "checked",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == f"/admin/user/{account_key.id()}"

    account = account_key.get()
    assert account is not None
    assert account.display_name == "Edited User"
    assert account.permissions == [AccountPermission.REVIEW_EVENT_MEDIA]


def test_user_lookup(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/user/lookup")
    assert resp.status_code == 200


def test_user_lookup_redirect(web_client: Client, login_gae_admin) -> None:
    account_key = create_accounts(n=1)[0]
    account = account_key.get()

    resp = web_client.post("/admin/user/lookup", data={"email": account.email})
    assert resp.status_code == 302
    assert resp.headers["Location"] == f"/admin/user/{account_key.id()}"


def test_user_lookup_no_match(web_client: Client, login_gae_admin) -> None:
    create_accounts(n=1)

    resp = web_client.post("/admin/user/lookup", data={"email": "foo@bar.com"})
    assert resp.status_code == 404


def test_user_lookup_no_param(web_client: Client, login_gae_admin) -> None:
    create_accounts(n=1)

    resp = web_client.post("/admin/user/lookup", data={})
    assert resp.status_code == 404


def test_user_permissions_list(web_client: Client, login_gae_admin) -> None:
    create_accounts(n=10, permissions=[AccountPermission.REVIEW_MEDIA])

    resp = web_client.get("/admin/users/permissions")
    assert resp.status_code == 200
