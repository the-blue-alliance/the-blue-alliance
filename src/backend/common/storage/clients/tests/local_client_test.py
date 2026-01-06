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
    assert isinstance(client, LocalStorageClient)
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

    mock_mkdir.assert_called_with(parents=True, exist_ok=True)
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

    mock_mkdir.assert_called_with(parents=True, exist_ok=True)
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
    assert client.read(file_name) == file_content.encode()


def test_get_files(tmp_path):
    tmp_path = Path(tmp_path)
    file_name = "some_file.json"
    file_content = "some_content"

    client = LocalStorageClient(tmp_path)
    assert client.get_files() == []
    client.write(file_name, file_content)
    assert client.get_files() == ["some_file.json"]
    # Add a directory - make sure we get only files
    (tmp_path / "some_dir").mkdir()
    assert client.get_files() == ["some_file.json"]


def test_get_files_prefix(tmp_path):
    tmp_path = Path(tmp_path)
    file_name = "some_file.json"
    file_content = "some_content"

    client = LocalStorageClient(tmp_path)
    assert client.get_files() == []
    client.write(file_name, file_content)
    assert client.get_files("foo") == []
    assert client.get_files("some") == ["some_file.json"]
