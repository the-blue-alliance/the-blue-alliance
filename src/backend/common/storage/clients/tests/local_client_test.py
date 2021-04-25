import tempfile
from pathlib import Path
from unittest.mock import patch

from backend.common.storage.clients.local_client import LocalStorageClient


def test_init():
    base_path = Path(tempfile.gettempdir())
    client = LocalStorageClient(base_path)
    assert client.base_path == base_path


def test_client_base_path(tmp_path):
    client = LocalStorageClient(tmp_path)
    assert type(client) is LocalStorageClient
    assert client.base_path == tmp_path


def test_write_mkdir():
    tmp_path = Path("some/fake/path")
    file_name = "some_file.json"
    file_content = "some_content"

    client = LocalStorageClient(tmp_path)

    with patch.object(Path, "mkdir") as mock_mkdir, patch.object(
        Path, "write_text"
    ) as mock_write_text:
        client.write(file_name, file_content)

    mock_mkdir.assert_called_with(tmp_path, parents=True)
    mock_write_text.assert_called_with(file_content)


def test_write(tmp_path):
    tmp_path = Path(tmp_path)
    file_name = "some_file.json"
    file_content = "some_content"

    client = LocalStorageClient(tmp_path)

    with patch.object(Path, "mkdir") as mock_mkdir, patch.object(
        Path, "write_text"
    ) as mock_write_text:
        client.write(file_name, file_content)

    mock_mkdir.assert_not_called()
    mock_write_text.assert_called_with(file_content)


def test_read_none(tmp_path):
    tmp_path = Path(tmp_path)
    file_name = "some_file.json"

    client = LocalStorageClient(tmp_path)
    assert client.read(file_name) is None


def test_read(tmp_path):
    tmp_path = Path(tmp_path)
    file_name = "some_file.json"
    file_content = "some_content"

    client = LocalStorageClient(tmp_path)
    assert client.read(file_name) is None
    client.write(file_name, file_content)
    assert client.read(file_name) == file_content
