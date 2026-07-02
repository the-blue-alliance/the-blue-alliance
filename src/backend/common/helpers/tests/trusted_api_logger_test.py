from unittest.mock import Mock, patch

import pytest
from flask import Flask, Request, Response

from backend.common.helpers.trusted_api_logger import TrustedApiLogger


@pytest.fixture
def app():
    """Create a test Flask app."""
    return Flask(__name__)


def create_mock_request(
    method: str = "POST",
    path: str = "/api/trusted/v1/event/2019nyny/team_list/update",
    data: bytes = b'{"test": "data"}',
    auth_id: str = "test_auth_id",
) -> Request:
    """Create a mock Flask request."""
    mock_request = Mock(spec=Request)
    mock_request.method = method
    mock_request.path = path
    mock_request.get_data.return_value = data
    mock_request.headers = {"X-TBA-Auth-Id": auth_id}
    return mock_request


def create_mock_response(status_code: int = 200) -> Response:
    """Create a mock Flask response."""
    mock_response = Mock(spec=Response)
    mock_response.status_code = status_code
    return mock_response


class TestTrustedApiLogger:
    def test_get_bucket(self) -> None:
        """Test getting the bucket name."""
        with patch(
            "backend.common.helpers.trusted_api_logger.Environment.project"
        ) as mock_project:
            mock_project.return_value = "test-project"
            bucket = TrustedApiLogger.get_bucket()
            assert bucket == "test-project-trustedapi-requests"

    def test_should_log_request_success(self) -> None:
        """Test that successful POST requests should be logged."""
        request = create_mock_request(method="POST", data=b'{"test": "data"}')
        response = create_mock_response(status_code=200)

        assert TrustedApiLogger.should_log_request(request, response) is True

    def test_should_log_request_patch(self) -> None:
        """Test that successful PATCH requests should be logged."""
        request = create_mock_request(method="PATCH", data=b'{"test": "data"}')
        response = create_mock_response(status_code=200)

        assert TrustedApiLogger.should_log_request(request, response) is True

    def test_should_log_request_delete(self) -> None:
        """Test that successful DELETE requests should be logged."""
        request = create_mock_request(method="DELETE", data=b'{"test": "data"}')
        response = create_mock_response(status_code=200)

        assert TrustedApiLogger.should_log_request(request, response) is True

    def test_should_not_log_get_request(self) -> None:
        """Test that GET requests should not be logged."""
        request = create_mock_request(method="GET", data=b"")
        response = create_mock_response(status_code=200)

        assert TrustedApiLogger.should_log_request(request, response) is False

    def test_should_not_log_failed_request(self) -> None:
        """Test that failed requests should not be logged."""
        request = create_mock_request(method="POST", data=b'{"test": "data"}')
        response = create_mock_response(status_code=401)

        assert TrustedApiLogger.should_log_request(request, response) is False

    def test_should_not_log_empty_body(self) -> None:
        """Test that requests with empty body should not be logged."""
        request = create_mock_request(method="POST", data=b"")
        response = create_mock_response(status_code=200)

        assert TrustedApiLogger.should_log_request(request, response) is False

    def test_log_request_success(self) -> None:
        """Test successfully logging a request."""
        request = create_mock_request(
            method="POST",
            path="/api/trusted/v1/event/2019nyny/team_list/update",
            data=b'{"test": "data"}',
            auth_id="test_auth_id",
        )
        response = create_mock_response(status_code=200)

        with patch(
            "backend.common.helpers.trusted_api_logger.storage_write"
        ) as mock_write:
            with patch(
                "backend.common.helpers.trusted_api_logger.Environment.project"
            ) as mock_project:
                with patch(
                    "backend.common.helpers.trusted_api_logger.current_user"
                ) as mock_user:
                    mock_project.return_value = "test-project"
                    mock_user.return_value = None

                    storage_path = TrustedApiLogger.log_request(request, response)

                    assert storage_path is not None
                    assert storage_path.startswith(
                        "api/trusted/v1/event/2019nyny/team_list/update/"
                    )
                    assert storage_path.endswith(".json")

                    # Verify storage_write was called
                    mock_write.assert_called_once()
                    call_args = mock_write.call_args

                    # Check storage path
                    assert call_args[0][0] == storage_path

                    # Check content
                    assert call_args[0][1] == b'{"test": "data"}'

                    # Check bucket
                    assert call_args[1]["bucket"] == "test-project-trustedapi-requests"

                    # Check content type
                    assert call_args[1]["content_type"] == "application/json"

                    # Check metadata
                    metadata = call_args[1]["metadata"]
                    assert metadata["X-TBA-Auth-Id"] == "test_auth_id"
                    assert metadata["method"] == "POST"
                    assert metadata["status_code"] == "200"

    def test_log_request_with_user(self) -> None:
        """Test logging a request with authenticated user."""
        request = create_mock_request(method="POST", data=b'{"test": "data"}')
        response = create_mock_response(status_code=200)

        mock_user = Mock()
        mock_user.uid = "user123"
        mock_user.email = "test@example.com"

        with patch(
            "backend.common.helpers.trusted_api_logger.storage_write"
        ) as mock_write:
            with patch(
                "backend.common.helpers.trusted_api_logger.Environment.project"
            ) as mock_project:
                with patch(
                    "backend.common.helpers.trusted_api_logger.current_user"
                ) as mock_current_user:
                    mock_project.return_value = "test-project"
                    mock_current_user.return_value = mock_user

                    storage_path = TrustedApiLogger.log_request(request, response)

                    assert storage_path is not None

                    # Check metadata includes user info
                    metadata = mock_write.call_args[1]["metadata"]
                    assert metadata["X-TBA-Auth-User"] == "user123"
                    assert metadata["X-TBA-Auth-User-Email"] == "test@example.com"

    def test_log_request_skips_non_loggable(self) -> None:
        """Test that non-loggable requests return None without calling storage."""
        request = create_mock_request(method="GET", data=b"")
        response = create_mock_response(status_code=200)

        with patch(
            "backend.common.helpers.trusted_api_logger.storage_write"
        ) as mock_write:
            storage_path = TrustedApiLogger.log_request(request, response)

            assert storage_path is None
            mock_write.assert_not_called()

    def test_log_request_handles_exception(self) -> None:
        """Test that exceptions during logging are handled gracefully."""
        request = create_mock_request(method="POST", data=b'{"test": "data"}')
        response = create_mock_response(status_code=200)

        with patch(
            "backend.common.helpers.trusted_api_logger.storage_write"
        ) as mock_write:
            mock_write.side_effect = Exception("Storage error")

            # Should return None instead of raising exception
            storage_path = TrustedApiLogger.log_request(request, response)
            assert storage_path is None
