import pytest
from werkzeug.test import Client


def test_root(api_client: Client) -> None:
    resp = api_client.get("/api/v3")
    assert resp.status_code == 200
