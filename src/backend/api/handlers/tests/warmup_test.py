from werkzeug.test import Client

from backend.api.handlers.warmup import warmup


def test_warmup_endpoint(api_client: Client) -> None:
    resp = api_client.get("/_ah/warmup")
    assert resp.status_code == 200


def test_warmup_direct() -> None:
    resp = warmup()
    assert resp.status_code == 200
