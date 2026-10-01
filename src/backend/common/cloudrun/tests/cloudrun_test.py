from unittest.mock import patch

import pytest
from _pytest.monkeypatch import MonkeyPatch

from backend.common import cloudrun
from backend.common.cloudrun.clients.local_client import LocalCloudRunClient
from backend.common.sitevars.google_cloudrun_config import (
    ContentType,
    GoogleCloudRunConfig,
)


@pytest.fixture
def not_unit_test(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TBA_UNIT_TEST", "false")
    monkeypatch.delenv("GAE_ENV", raising=False)


def test_client_for_unit_test() -> None:
    assert isinstance(cloudrun._client_for_env(), LocalCloudRunClient)


def test_client_for_dev(not_unit_test, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "localdev")
    assert isinstance(cloudrun._client_for_env(), LocalCloudRunClient)


def test_client_requires_project(not_unit_test, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT"):
        cloudrun._client_for_env()


def test_client_requires_region(
    not_unit_test, monkeypatch: MonkeyPatch, ndb_stub
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    with pytest.raises(ValueError, match="GoogleCloudRunConfig.region"):
        cloudrun._client_for_env()


def test_client_for_prod(not_unit_test, monkeypatch: MonkeyPatch, ndb_stub) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    GoogleCloudRunConfig.put(ContentType(cloudrun_region="us-central1"))
    with patch(
        "backend.common.cloudrun.clients.gcloud_client.GCloudRunClient"
    ) as mock_client:
        client = cloudrun._client_for_env()
    mock_client.assert_called_once_with("test-project", "us-central1")
    assert client is mock_client.return_value


def test_start_job_and_get_status() -> None:
    assert cloudrun.start_job("job", ["--flag"], {"K": "V"}) == "test-execution-id"
    assert cloudrun.get_job_status("job", "test-execution-id") == {
        "state": "SUCCEEDED",
        "message": "Job completed successfully (1/1 tasks succeeded)",
        "is_complete": True,
    }
