from api_main import app


def test_root() -> None:
    client = app.test_client()
    resp = client.get("/api/v3")
    assert resp.status_code == 200
