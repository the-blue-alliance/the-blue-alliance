from unittest.mock import patch

from backend.common.helpers.fms_companion_helper import FMSCompanionHelper

MODULE = "backend.common.helpers.fms_companion_helper"


def test_get_newest_file_path() -> None:
    with patch(
        f"{MODULE}.storage_get_files",
        return_value=[
            "fms_companion/2024test/fms_companion.2.db",
            "fms_companion/2024test/fms_companion.1.db",
        ],
    ):
        assert (
            FMSCompanionHelper.get_newest_file_path("2024test")
            == "fms_companion/2024test/fms_companion.2.db"
        )


def test_get_newest_file_path_no_files() -> None:
    with patch(f"{MODULE}.storage_get_files", return_value=[]):
        assert FMSCompanionHelper.get_newest_file_path("2024test") is None


def test_get_newest_file_path_storage_error() -> None:
    with patch(f"{MODULE}.storage_get_files", side_effect=Exception("gcs down")):
        assert FMSCompanionHelper.get_newest_file_path("2024test") is None


def test_read_newest_companion_db() -> None:
    with (
        patch.object(FMSCompanionHelper, "get_newest_file_path", return_value="f.db"),
        patch(f"{MODULE}.storage_read", return_value=b"sqlite") as mock_read,
    ):
        assert FMSCompanionHelper.read_newest_companion_db("2024test") == b"sqlite"
    assert mock_read.call_args[0][0] == "f.db"


def test_read_newest_companion_db_no_file() -> None:
    with patch.object(FMSCompanionHelper, "get_newest_file_path", return_value=None):
        assert FMSCompanionHelper.read_newest_companion_db("2024test") is None


def test_read_newest_companion_db_storage_error() -> None:
    with (
        patch.object(FMSCompanionHelper, "get_newest_file_path", return_value="f.db"),
        patch(f"{MODULE}.storage_read", side_effect=Exception("gcs down")),
    ):
        assert FMSCompanionHelper.read_newest_companion_db("2024test") is None
