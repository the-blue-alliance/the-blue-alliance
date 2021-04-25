from typing import Optional

from google.cloud import storage

from backend.common.storage.clients.storage_client import StorageClient


class GCloudStorageClient(StorageClient):
    def __init__(self, project: str) -> None:
        client = storage.Client(project=project)
        self.bucket = client.get_bucket(f"{project}.appspot.com")

    def write(self, file_name: str, content: str) -> None:
        blob = self.bucket.blob(file_name)
        blob.upload_from_string(content)

    def read(self, file_name: str) -> Optional[str]:
        blob = self.bucket.get_blob(file_name)
        if blob:
            with blob.open("r") as f:
                return f.read()

        return None
