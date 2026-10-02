from unittest.mock import Mock, patch

from backend.common.storage.clients.cloudstorage_client import CloudStorageClient


def test_get_files_non_recursive_uses_delimiter() -> None:
    bucket = "tba-unit-tests.appspot.com"
    path = "api/trusted/v1/event/2025inbbb/"
    file_path = "api/trusted/v1/event/2025inbbb/2026-03-06T04:03:36.168663+00:00.json"

    mock_file = Mock()
    mock_file.filename = f"/{bucket}/{file_path}"
    mock_file.is_dir = False

    client = CloudStorageClient(bucket)

    with patch(
        "backend.common.storage.clients.cloudstorage_client.listbucket",
        return_value=[mock_file],
    ) as mock_listbucket:
        files = client.get_files(path)

    assert files == [file_path]
    mock_listbucket.assert_called_once_with(
        f"/{bucket}/api/trusted/v1/event/2025inbbb/",
        delimiter="/",
    )


def test_get_files_recursive_lists_nested_files() -> None:
    bucket = "tba-unit-tests.appspot.com"
    path = "api/trusted/v1/event/2025inbbb/"
    nested_file_path = (
        "api/trusted/v1/event/2025inbbb/match_videos/add/"
        "2026-03-06T04:14:28.343659+00:00.json"
    )

    mock_nested_file = Mock()
    mock_nested_file.filename = f"/{bucket}/{nested_file_path}"
    mock_nested_file.is_dir = False

    client = CloudStorageClient(bucket)

    with patch(
        "backend.common.storage.clients.cloudstorage_client.listbucket",
        return_value=[mock_nested_file],
    ) as mock_listbucket:
        files = client.get_files(path, recursive=True)

    assert files == [nested_file_path]
    mock_listbucket.assert_called_once_with(
        f"/{bucket}/api/trusted/v1/event/2025inbbb/",
        delimiter=None,
    )
