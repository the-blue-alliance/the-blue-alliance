import re
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from _pytest.monkeypatch import MonkeyPatch

from backend.common import storage
from backend.common.storage.clients.gcloud_client import GCloudStorageClient
from backend.common.storage.clients.in_memory_client import InMemoryClient
from backend.common.storage.clients.local_client import LocalStorageClient


@pytest.fixture
def set_override_tba_test(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TBA_UNIT_TEST", "false")


@pytest.fixture
def set_dev(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "localdev")


@pytest.fixture
def set_prod(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "standard")


@pytest.fixture
def set_project(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "tbatv-prod-hrd")


@pytest.fixture
def set_storage_mode_remote(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_MODE", "remote")


@pytest.fixture
def set_storage_path(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_PATH", "some/fake/path")


def test_client_for_env_unit_test():
    client = storage._client_for_env()
    assert type(client) is InMemoryClient


def test_client_for_env_unit_test_remote(set_storage_mode_remote):
    client = storage._client_for_env()
    assert type(client) is InMemoryClient


def test_client_for_env_dev(set_override_tba_test, set_dev):
    client = storage._client_for_env()
    assert type(client) is LocalStorageClient
    assert client.base_path == Path(tempfile.gettempdir())


def test_client_for_env_dev_path(set_override_tba_test, set_dev, set_storage_path):
    client = storage._client_for_env()
    assert type(client) is LocalStorageClient
    assert client.base_path == Path("some/fake/path")


def test_client_for_env_dev_remote_no_project(
    set_override_tba_test, set_dev, set_storage_mode_remote
):
    with pytest.raises(
        Exception,
        match=re.escape(
            "Environment.project (GOOGLE_CLOUD_PROJECT) unset - should be set when using remote storage mode."
        ),
    ):
        storage._client_for_env()


def test_client_for_env_dev_remote(
    set_override_tba_test, set_dev, set_storage_mode_remote, set_project
):
    with patch.object(
        GCloudStorageClient, "__init__", return_value=None
    ) as gcloud_storage_client_init:
        client = storage._client_for_env()

    gcloud_storage_client_init.assert_called_with("tbatv-prod-hrd")
    assert type(client) is GCloudStorageClient


def test_client_for_env_production_no_project(set_override_tba_test, set_prod):
    with pytest.raises(
        Exception,
        match=re.escape(
            "Environment.project (GOOGLE_CLOUD_PROJECT) unset - should be set in production."
        ),
    ):
        storage._client_for_env()


def test_client_for_env_production(set_override_tba_test, set_prod, set_project):
    with patch.object(
        GCloudStorageClient, "__init__", return_value=None
    ) as gcloud_storage_client_init:
        client = storage._client_for_env()

    gcloud_storage_client_init.assert_called_with("tbatv-prod-hrd")
    assert type(client) is GCloudStorageClient


def test_write():
    file_name = "some_file.json"
    content = "some_content"

    client = Mock()
    with patch.object(storage, "_client_for_env", return_value=client):
        storage.write(file_name, content)

    client.write.assert_called_with(file_name, content)


def test_read():
    file_name = "some_file.json"

    client = Mock()
    with patch.object(storage, "_client_for_env", return_value=client):
        storage.read(file_name)

    client.read.assert_called_with(file_name)


def test_get_files():
    path = "abc/"

    client = Mock()
    with patch.object(storage, "_client_for_env", return_value=client):
        storage.get_files(path)

    client.get_files.assert_called_with(path)
