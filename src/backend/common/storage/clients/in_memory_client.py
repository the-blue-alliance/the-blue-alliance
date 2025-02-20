from typing import Dict, List, Optional

from pyre_extensions import none_throws

from backend.common.storage.clients.storage_client import StorageClient


class InMemoryClient(StorageClient):
    CLIENT: Optional["InMemoryClient"] = None

    data: Dict[str, str]

    @classmethod
    def get(cls) -> "InMemoryClient":
        if cls.CLIENT is None:
            cls.CLIENT = InMemoryClient()
        return none_throws(cls.CLIENT)

    def __init__(self) -> None:
        self.data = {}

    def write(self, file_name: str, content: str) -> None:
        self.data[file_name] = content

    def read(self, file_name: str) -> Optional[str]:
        return self.data.get(file_name)

    def get_files(self, path: Optional[str] = None) -> List[str]:
        return [p for p in self.data.keys() if path is None or p.startswith(path)]
