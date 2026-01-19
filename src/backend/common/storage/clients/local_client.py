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

    def get_files(self, path: Optional[str] = None) -> List[str]:
        logging.info(f"Getting files from local storage with prefix: {path}")
        if not self.base_path.exists():
            logging.info(f"Base path {self.base_path} does not exist.")
            return []

        # Get all files recursively
        all_files = []
        for p in self.base_path.rglob("*"):
            if p.is_file():
                # Get relative path from base_path
                rel_path = str(p.relative_to(self.base_path))
                # If prefix is specified, filter by it
                if path is None or rel_path.startswith(path):
                    all_files.append(rel_path)

        return all_files
