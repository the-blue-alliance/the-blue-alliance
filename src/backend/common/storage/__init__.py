from typing import List, Optional

from backend.common.environment import Environment, EnvironmentMode
from backend.common.storage.clients.gcloud_client import GCloudStorageClient
from backend.common.storage.clients.in_memory_client import InMemoryClient
from backend.common.storage.clients.local_client import LocalStorageClient
from backend.common.storage.clients.storage_client import StorageClient


def _client_for_env(bucket: str | None = None) -> StorageClient:
    storage_mode = Environment.storage_mode()

    if Environment.is_unit_test():
        return InMemoryClient.get()

    project = Environment.project()
    if not project:
        detail_string = "should be set in production"
        if storage_mode == EnvironmentMode.REMOTE:
            detail_string = "should be set when using remote storage mode"
        raise ValueError(
            f"Environment.project (GOOGLE_CLOUD_PROJECT) unset - {detail_string}."
        )
    bucket = bucket or f"{project}.appspot.com"

    if Environment.is_dev() and storage_mode == EnvironmentMode.LOCAL:
        storage_path = Environment.storage_path() / project / bucket
        return LocalStorageClient(storage_path)

    return GCloudStorageClient(project, bucket)


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
