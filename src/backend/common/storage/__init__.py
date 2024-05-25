from typing import List, Optional

from backend.common.environment import Environment, EnvironmentMode
from backend.common.storage.clients.gcloud_client import GCloudStorageClient
from backend.common.storage.clients.in_memory_client import InMemoryClient
from backend.common.storage.clients.local_client import LocalStorageClient
from backend.common.storage.clients.storage_client import StorageClient


def _client_for_env() -> StorageClient:
    storage_path = Environment.storage_path()

    if Environment.is_unit_test():
        return InMemoryClient.get()

    storage_mode = Environment.storage_mode()
    if Environment.is_dev() and storage_mode == EnvironmentMode.LOCAL:
        return LocalStorageClient(storage_path)

    project = Environment.project()
    if not project:
        detail_string = "should be set in production"
        if storage_mode == EnvironmentMode.REMOTE:
            detail_string = "should be set when using remote storage mode"
        raise Exception(
            f"Environment.project (GOOGLE_CLOUD_PROJECT) unset - {detail_string}."
        )

    return GCloudStorageClient(project)


def write(file_name: str, content: str) -> None:
    client = _client_for_env()
    client.write(file_name, content)


def read(file_name: str) -> Optional[str]:
    client = _client_for_env()
    return client.read(file_name)


def get_files(path: Optional[str] = None) -> List[str]:
    client = _client_for_env()
    return client.get_files(path)
