from werkzeug.test import Client

from backend.common.models.sitevar import Sitevar


def test_sitevars_list_empty(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/sitevars")
    assert resp.status_code == 200


def test_sitevars_list(web_client: Client, login_gae_admin) -> None:
    Sitevar(
        id="test_sitevar",
    ).put()
    resp = web_client.get("/admin/sitevars")
    assert resp.status_code == 200


def test_sitevar_create(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/sitevar/create")
    assert resp.status_code == 200


def test_sitevar_create_post(web_client: Client, login_gae_admin) -> None:
    resp = web_client.post(
        "/admin/sitevar/edit/test_sitevar",
        data={"key": "test_sitevar", "description": "test", "values_json": "{}"},
    )
    assert resp.status_code == 302
    assert (
        resp.headers["Location"]
        == "http://localhost/admin/sitevar/edit/test_sitevar?success=true"
    )

    sv = Sitevar.get_by_id("test_sitevar")
    assert sv is not None
    assert sv.description == "test"
    assert sv.contents == {}


def test_sitevar_edit_post(web_client: Client, login_gae_admin) -> None:
    Sitevar(
        id="test_sitevar",
    ).put()
    resp = web_client.post(
        "/admin/sitevar/edit/test_sitevar",
        data={"key": "test_sitevar", "description": "test", "values_json": "[]"},
    )
    assert resp.status_code == 302
    assert (
        resp.headers["Location"]
        == "http://localhost/admin/sitevar/edit/test_sitevar?success=true"
    )

    sv = Sitevar.get_by_id("test_sitevar")
    assert sv is not None
    assert sv.description == "test"
    assert sv.contents == []
