from typing import List, Optional

from backend.common.environment import Environment
from backend.common.storage.clients.cloudstorage_client import CloudStorageClient
from backend.common.storage.clients.storage_client import StorageClient


def _client_for_env(bucket: str | None = None) -> StorageClient:
    project = Environment.project()
    if not project:
        raise ValueError("Environment.project (GOOGLE_CLOUD_PROJECT) unset")
    bucket = bucket or f"{project}.appspot.com"
    return CloudStorageClient(bucket=bucket)


def write(
    file_name: str,
    content: str | bytes,
    content_type: str = "text/plain",
    bucket: str | None = None,
    metadata: dict[str, str | None] | None = None,
) -> None:
    client = _client_for_env(bucket)
    client.write(file_name, content, content_type, metadata)


def read(file_name: str, bucket: str | None = None) -> Optional[str | bytes]:
    client = _client_for_env(bucket)
    return client.read(file_name)


def get_files(path: Optional[str] = None, bucket: str | None = None) -> List[str]:
    client = _client_for_env(bucket)
    return client.get_files(path)
