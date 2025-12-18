import logging
from pathlib import Path
from typing import List, Optional

from backend.common.storage.clients.storage_client import StorageClient


class LocalStorageClient(StorageClient):
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def write(
        self,
        file_name: str,
        content: str | bytes,
        content_type: str = "text/plain",
        metadata: dict[str, str | None] | None = None,
    ) -> None:
        path = self.base_path / Path(file_name)
        logging.info(f"Writing file to local storage at {path}")
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content)

    def read(self, file_name: str) -> Optional[str | bytes]:
        path = self.base_path / file_name
        if path.exists():
            with path.open(mode="rb") as f:
                return f.read()

        return None

    def get_files(self, path_name: Optional[str] = None) -> List[str]:
        path = self.base_path / Path(path_name)
        logging.info(f"Getting files from local storage at {path}")
        if not path.exists():
            logging.info(f"Base path {path} does not exist.")
            return []
        return [path_name + "/" + p.name for p in path.iterdir() if p.is_file()]
