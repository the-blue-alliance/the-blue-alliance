from google.auth.credentials import Credentials
from google.cloud import storage

from backend.common.storage.clients.storage_client import StorageClient


class GCloudStorageClient(StorageClient):
    def __init__(self, project: str, credentials: Credentials | None = None) -> None:
        self.client = storage.Client(project=project, credentials=credentials)
        self.bucket = self.client.get_bucket(f"{project}.appspot.com")

    def write(self, file_name: str, content: str) -> None:
        blob = self.bucket.blob(file_name)
        blob.upload_from_string(content)

    def read(self, file_name: str) -> str | None:
        blob = self.bucket.get_blob(file_name)
        if blob:
            with blob.open("r") as f:
                return f.read()

        return None

    def get_files(self, path: str | None = None) -> list[str]:
        return [
            blob.name
            for blob in self.client.list_blobs(
                self.bucket, prefix=path, delimiter="/" if path else None
            )
        ]
