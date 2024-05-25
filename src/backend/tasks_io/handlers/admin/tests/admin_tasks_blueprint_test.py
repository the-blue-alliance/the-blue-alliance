from werkzeug.test import Client


def test_not_logged_in_no_user(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/admin/do/nothing")
    assert resp.status_code == 401


def test_not_logged_in_not_admin(tasks_client: Client, login_gae_user) -> None:
    resp = tasks_client.get("/tasks/admin/do/nothing")
    assert resp.status_code == 401


def test_not_logged_in_admin(tasks_client: Client, login_gae_admin) -> None:
    resp = tasks_client.get("/tasks/admin/do/nothing")
    assert resp.status_code == 200
