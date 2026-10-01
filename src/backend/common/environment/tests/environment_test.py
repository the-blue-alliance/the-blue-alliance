import tempfile
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from backend.common.environment import Environment
from backend.common.environment import environment as environment_module
from backend.common.environment.environment import EnvironmentMode


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


def test_project(set_project) -> None:
    assert Environment.project() == "tbatv-prod-hrd"


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


def test_strtobool() -> None:
    assert Environment._strtobool("") is False
    assert Environment._strtobool("yes") is True
    assert Environment._strtobool("off") is False


def test_is_prod_project(monkeypatch: MonkeyPatch) -> None:
    assert Environment.is_prod_project() is False
    monkeypatch.setenv("GAE_ENV", "standard")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "someone-elses-project")
    assert Environment.is_prod_project() is False
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "tbatv-prod-hrd")
    assert Environment.is_prod_project() is True


def test_log_levels(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TBA_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("NDB_LOG_LEVEL", "WARNING")
    assert Environment.log_level() == "DEBUG"
    assert Environment.ndb_log_level() == "WARNING"


def test_flask_secret_key(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    assert Environment.flask_secret_key() == Environment.DEFAULT_FLASK_SECRET_KEY
    monkeypatch.setenv("FLASK_SECRET_KEY", "shh")
    assert Environment.flask_secret_key() == "shh"


def test_cache_flags(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("FLASK_RESPONSE_CACHE_ENABLED", raising=False)
    monkeypatch.delenv("CACHE_CONTROL_HEADER_ENABLED", raising=False)
    assert Environment.flask_response_cache_enabled() is True
    assert Environment.cache_control_header_enabled() is True
    monkeypatch.setenv("FLASK_RESPONSE_CACHE_ENABLED", "false")
    monkeypatch.setenv("CACHE_CONTROL_HEADER_ENABLED", "0")
    assert Environment.flask_response_cache_enabled() is False
    assert Environment.cache_control_header_enabled() is False


def test_storage_mode(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("STORAGE_MODE", raising=False)
    assert Environment.storage_mode() == EnvironmentMode.LOCAL
    monkeypatch.setenv("STORAGE_MODE", "remote")
    assert Environment.storage_mode() == EnvironmentMode.REMOTE


@pytest.fixture
def fake_repo(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    """
    Point the environment module at a fake checkout, so that
    parents[3] (where COMMIT lives) is tmp_path/src and
    parents[4] (where .git lives) is tmp_path.
    """
    module_file = tmp_path / "src" / "backend" / "common" / "environment" / "e.py"
    monkeypatch.setattr(environment_module, "__file__", str(module_file))
    monkeypatch.setattr(Environment, "_commit_info", None)
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()
    return tmp_path


def test_commit_info_from_commit_file(fake_repo: Path) -> None:
    (fake_repo / "src" / "COMMIT").write_text("abc123 Fix the thing\n")
    assert Environment.commit_info() == ("abc123", "Fix the thing")
    # Cached after the first read
    (fake_repo / "src" / "COMMIT").write_text("def456 Other\n")
    assert Environment.commit_info() == ("abc123", "Fix the thing")


def test_commit_info_from_commit_file_sha_only(fake_repo: Path) -> None:
    (fake_repo / "src" / "COMMIT").write_text("abc123")
    assert Environment.commit_info() == ("abc123", None)


def test_commit_info_empty_commit_file_falls_back_to_git(fake_repo: Path) -> None:
    (fake_repo / "src" / "COMMIT").write_text("  \n")
    (fake_repo / ".git" / "HEAD").write_text("deadbeef\n")
    assert Environment.commit_info() == ("deadbeef", None)


def test_commit_info_nothing_available(fake_repo: Path) -> None:
    assert Environment.commit_info() == (None, None)


def test_read_git_head_loose_ref(fake_repo: Path) -> None:
    (fake_repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    (fake_repo / ".git" / "refs" / "heads").mkdir(parents=True)
    (fake_repo / ".git" / "refs" / "heads" / "main").write_text("cafef00d\n")
    assert Environment._read_git_head() == "cafef00d"


def test_read_git_head_packed_ref(fake_repo: Path) -> None:
    (fake_repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    (fake_repo / ".git" / "packed-refs").write_text(
        "# pack-refs with: peeled fully-peeled sorted\n"
        "1111 refs/heads/other\n"
        "2222 refs/heads/main\n"
    )
    assert Environment._read_git_head() == "2222"


def test_read_git_head_ref_missing(fake_repo: Path) -> None:
    (fake_repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    assert Environment._read_git_head() is None

    (fake_repo / ".git" / "packed-refs").write_text("1111 refs/heads/other\n")
    assert Environment._read_git_head() is None
