from unittest.mock import patch

from werkzeug.test import Client

from backend.api.client_api_auth_helper import ClientApiAuthHelper
from backend.common import auth


def test_no_headers(api_client: Client) -> None:
    with api_client.application.test_request_context(headers=None):  # pyre-ignore[16]
        user = ClientApiAuthHelper.get_current_user()
        assert user is None


def test_malformed_header(api_client: Client) -> None:
    with api_client.application.test_request_context(  # pyre-ignore[16]
        headers={"Authorization": "badly_formatted"}
    ):
        user = ClientApiAuthHelper.get_current_user()
        assert user is None


def test_valid_header(api_client: Client) -> None:
    with api_client.application.test_request_context(  # pyre-ignore[16]
        headers={"Authorization": "Bearer abc123"}
    ), patch.object(auth, "_verify_id_token") as mock_verify_id_token:
        mock_verify_id_token.return_value = {}
        user = ClientApiAuthHelper.get_current_user()
        assert user is not None
        assert user._session_claims == {}


def test_invalid_header(api_client: Client) -> None:
    with api_client.application.test_request_context(  # pyre-ignore[16]
        headers={"Authorization": "Bearer abc123"}
    ), patch.object(auth, "_verify_id_token") as mock_verify_id_token:
        mock_verify_id_token.return_value = None
        user = ClientApiAuthHelper.get_current_user()
        assert user is None
