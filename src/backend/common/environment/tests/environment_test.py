import tempfile
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from backend.common.environment import Environment


@pytest.fixture
def set_unit_test(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TBA_UNIT_TEST", "false")


@pytest.fixture
def set_firebase_auth_emulator_host(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")


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
def set_service(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_SERVICE", "default")


@pytest.fixture
def set_save_frc_api_response(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")


def test_unit_tests() -> None:
    assert Environment.is_unit_test() is True


def test_unit_tests_false(set_unit_test) -> None:
    assert Environment.is_unit_test() is False


def test_dev_env(set_dev) -> None:
    assert Environment.is_dev() is True
    assert Environment.is_prod() is False


def test_prod_env(set_prod) -> None:
    assert Environment.is_dev() is False
    assert Environment.is_prod() is True


def test_project_none() -> None:
    assert Environment.project() is None


def test_project(set_project) -> None:
    assert Environment.project() == "tbatv-prod-hrd"


def test_service_none() -> None:
    assert Environment.service() is None


def test_service(set_service) -> None:
    assert Environment.service() == "default"


def test_other_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "something")
    assert Environment.is_dev() is False
    assert Environment.is_prod() is False


def test_storage_path_tmp(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "something")
    assert Environment.storage_path() == Path(tempfile.gettempdir())


def test_storage_path(monkeypatch: MonkeyPatch) -> None:
    some_path = "some/path/here"
    monkeypatch.setenv("STORAGE_PATH", some_path)
    assert Environment.storage_path() == Path(some_path)


def test_auth_emulator_host_none() -> None:
    assert Environment.auth_emulator_host() is None


def test_auth_emulator_host(set_firebase_auth_emulator_host) -> None:
    assert Environment.auth_emulator_host() == "localhost:9099"


def test_save_frc_api_response_default() -> None:
    assert Environment.save_frc_api_response() is False


def test_save_frc_api_response(set_save_frc_api_response) -> None:
    assert Environment.save_frc_api_response()


def test_save_frc_api_response_prod(set_prod) -> None:
    assert Environment.save_frc_api_response()
