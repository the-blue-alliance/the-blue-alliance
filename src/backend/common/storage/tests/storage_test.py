from unittest.mock import Mock, patch

import pytest
from _pytest.monkeypatch import MonkeyPatch

from backend.common import storage


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


def test_write():
    file_name = "some_file.json"
    content = "some_content"

    client = Mock()
    with patch.object(storage, "_client_for_env", return_value=client):
        storage.write(file_name, content)

    client.write.assert_called_with(file_name, content, "text/plain", None)


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
