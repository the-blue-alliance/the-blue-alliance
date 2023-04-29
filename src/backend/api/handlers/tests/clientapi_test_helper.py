import json
from typing import Any

from pyre_extensions import safe_json
from werkzeug.test import Client

from backend.api.client_api_types import BaseResponse


def make_clientapi_request(api_client: Client, endpoint: str, req: Any) -> BaseResponse:
    req_body = json.dumps(req)
    resp = api_client.post("/clientapi/tbaClient/v9" + endpoint, data=req_body)
    assert resp.status_code == 200
    return safe_json.loads(resp.data, BaseResponse)
