from werkzeug.test import Client


def test_api_auth_add(login_gae_admin, web_client: Client) -> None:
    resp = web_client.get("/admin/api_auth/add")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert 'name="event_list_str"' in content
    assert 'name="event_list_str" placeholder="2014cc,2014mttd" value=""' in content


def test_api_auth_add_with_event_key(login_gae_admin, web_client: Client) -> None:
    resp = web_client.get("/admin/api_auth/add?event_key=2020nyny")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert 'value="2020nyny"' in content
