import abc


class StorageClient(abc.ABC):
    @abc.abstractmethod
    def write(self, file_name: str, content: str) -> None: ...

    @abc.abstractmethod
    def read(self, file_name: str) -> str | None: ...

    @abc.abstractmethod
    def get_files(self, path: str | None) -> list[str]: ...
