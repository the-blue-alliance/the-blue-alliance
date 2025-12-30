from pathlib import Path

from backend.common.storage.clients.cloudstorage import (
    listbucket,
    NotFoundError,
    open as gcs_open,
)
from backend.common.storage.clients.storage_client import StorageClient


class CloudStorageClient(StorageClient):

    def __init__(
        self,
        bucket: str,
    ) -> None:
        self.bucket = bucket

    def write(
        self,
        file_name: str,
        content: str | bytes,
        content_type: str = "text/plain",
        metadata: dict[str, str | None] | None = None,
    ) -> None:
        path = Path(self.bucket) / Path(file_name)
        with gcs_open(
            f"/{str(path)}",
            mode="wb",
            content_type=content_type,
            options={
                "x-goog-meta-" + k: v for k, v in (metadata or {}).items() if k and v
            },
        ) as f:
            f.write(content)

    def read(self, file_name: str) -> str | bytes | None:
        try:
            with gcs_open(f"/{self.bucket}/{file_name}", mode="rb") as f:
                return f.read()
        except NotFoundError:
            return None

    def get_files(self, path: str | None = None) -> list[str]:
        list_path = Path(self.bucket)
        if path:
            list_path /= Path(path)
        return [
            obj.filename.lstrip(f"/{self.bucket}/")
            for obj in listbucket(
                f"/{str(list_path)}/",
                delimiter="/" if path else None,
            )
            if not obj.is_dir
        ]
