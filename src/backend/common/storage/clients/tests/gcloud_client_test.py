from unittest.mock import Mock, patch

from google.cloud import storage
from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket

from backend.common.storage.clients.gcloud_client import GCloudStorageClient


def test_init():
    project = "tba-unit-tests"
    mock_bucket = Mock(spec=Bucket)

    with patch.object(
        storage.Client, "__init__", return_value=None
    ) as mock_client_init, patch.object(
        storage.Client, "get_bucket", return_value=mock_bucket
    ) as mock_get_bucket:
        client = GCloudStorageClient(project)

    mock_client_init.assert_called_with(project=project, credentials=None)
    mock_get_bucket.assert_called_with("tba-unit-tests.appspot.com")
    assert client.bucket == mock_bucket


def test_write():
    mock_blob = Mock()

    mock_bucket = Mock(spec=Bucket)
    mock_bucket.configure_mock(**{"blob.return_value": mock_blob})

    file_name = "some_file.json"
    file_content = "some_content"

    with patch.object(storage.Client, "__init__", return_value=None), patch.object(
        storage.Client, "get_bucket", return_value=mock_bucket
    ):
        client = GCloudStorageClient("tba-unit-tests")

    client.write(file_name, file_content)
    mock_bucket.blob.assert_called_with(file_name)
    mock_blob.upload_from_string.assert_called_with(file_content)


def test_read_none():
    file_name = "some_file.json"

    mock_bucket = Mock(spec=Bucket)
    mock_bucket.configure_mock(**{"get_blob.return_value": None})

    with patch.object(storage.Client, "__init__", return_value=None), patch.object(
        storage.Client, "get_bucket", return_value=mock_bucket
    ):
        client = GCloudStorageClient("tba-unit-tests")

    assert client.read(file_name) is None
    mock_bucket.get_blob.assert_called_with(file_name)


def test_read():
    file_name = "some_file.json"
    mock_content = "some_content"

    mock_file = Mock()
    mock_file.configure_mock(**{"read.return_value": mock_content})

    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_file)
    mock_context.__exit__ = Mock(return_value=False)

    mock_blob = Mock()
    mock_blob.configure_mock(**{"open.return_value": mock_context})

    mock_bucket = Mock(spec=Bucket)
    mock_bucket.configure_mock(**{"get_blob.return_value": mock_blob})

    with patch.object(storage.Client, "__init__", return_value=None), patch.object(
        storage.Client, "get_bucket", return_value=mock_bucket
    ):
        client = GCloudStorageClient("tba-unit-tests")

    assert client.read("some_file.json") == mock_content
    mock_bucket.get_blob.assert_called_with(file_name)
    mock_blob.open.assert_called_with("r")


def test_get_files():
    file_name = "some_file.json"

    mock_blob = Mock(spec=Blob)
    mock_blob.name = file_name

    mock_bucket = Mock(spec=Bucket)

    with patch.object(storage.Client, "__init__", return_value=None), patch.object(
        storage.Client, "get_bucket", return_value=mock_bucket
    ):
        client = GCloudStorageClient("tba-unit-tests")

    with patch.object(
        client.client, "list_blobs", return_value=[mock_blob]
    ) as mock_list_blobs:
        files = client.get_files()

    assert files == [file_name]
    mock_list_blobs.assert_called_once_with(mock_bucket, prefix=None, delimiter=None)
