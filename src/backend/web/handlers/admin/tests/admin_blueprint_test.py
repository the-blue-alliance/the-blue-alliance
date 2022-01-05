from werkzeug.test import Client


def test_not_logged_in_no_user(web_client: Client) -> None:
    resp = web_client.get("/admin/tasks")
    assert resp.status_code == 401


def test_not_logged_in_not_admin(web_client: Client, login_gae_user) -> None:
    resp = web_client.get("/admin/tasks")
    assert resp.status_code == 401


def test_not_logged_in_admin(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/tasks")
    assert resp.status_code == 200
