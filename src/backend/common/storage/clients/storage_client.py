import abc
from typing import List, Optional


class StorageClient(abc.ABC):
    @abc.abstractmethod
    def write(self, file_name: str, content: str) -> None: ...

    @abc.abstractmethod
    def read(self, file_name: str) -> Optional[str]: ...

    @abc.abstractmethod
    def get_files(self, path: Optional[str]) -> List[str]: ...
