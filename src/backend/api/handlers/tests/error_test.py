import json
from werkzeug.test import Client


def test_handle_404(api_client: Client) -> None:
    resp = api_client.get("/asdf")
    assert resp.status_code == 404
    assert "Error" in json.loads(resp.data)
