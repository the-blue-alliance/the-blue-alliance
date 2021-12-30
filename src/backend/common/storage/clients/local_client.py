from pathlib import Path
from typing import List, Optional

from backend.common.storage.clients.storage_client import StorageClient


class LocalStorageClient(StorageClient):
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def write(self, file_name: str, content: str) -> None:
        path = self.base_path / file_name
        if not path.parent.exists():
            Path.mkdir(path.parent, parents=True)

        path.write_text(content)

    def read(self, file_name: str) -> Optional[str]:
        path = self.base_path / file_name
        if path.exists():
            with path.open() as f:
                return f.read()

        return None

    def get_files(self, path: Optional[str] = None) -> List[str]:
        return [
            p.name
            for p in self.base_path.iterdir()
            if p.is_file()
            if path is None or p.name.startswith(path)
        ]
