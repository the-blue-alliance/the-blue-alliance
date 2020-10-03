import pytest
from _pytest.monkeypatch import MonkeyPatch

from backend.common.environment import Environment, EnvironmentMode


@pytest.fixture
def set_dev(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "localdev")


@pytest.fixture
def set_prod(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "standard")


@pytest.fixture
def set_tasks_local(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TASKS_MODE", "local")


@pytest.fixture
def set_tasks_remote(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TASKS_MODE", "remote")


def test_dev_env(set_dev) -> None:
    assert Environment.is_dev() is True
    assert Environment.is_prod() is False


def test_prod_env(set_prod) -> None:
    assert Environment.is_dev() is False
    assert Environment.is_prod() is True


def test_tasks_mode_prod(set_prod) -> None:
    assert Environment.tasks_mode() is EnvironmentMode.REMOTE


def test_tasks_mode_local_empty() -> None:
    assert Environment.tasks_mode() is EnvironmentMode.LOCAL


def test_tasks_mode_local(set_tasks_local) -> None:
    assert Environment.tasks_mode() is EnvironmentMode.LOCAL


def test_tasks_mode_remote(set_tasks_remote) -> None:
    assert Environment.tasks_mode() is EnvironmentMode.REMOTE


def test_other_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "something")
    assert Environment.is_dev() is False
    assert Environment.is_prod() is False
