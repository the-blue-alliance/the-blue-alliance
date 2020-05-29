from default.main import app


def test_root() -> None:
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 404
