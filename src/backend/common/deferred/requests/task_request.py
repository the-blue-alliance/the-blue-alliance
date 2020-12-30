import abc
from typing import Dict, Optional


class TaskRequest(abc.ABC):

    headers: Dict[str, str]
    body: bytes
    service: Optional[str]

    def __init__(
        self,
        url: str,
        headers: Dict[str, str],
        body: bytes,
        service: Optional[str] = None,
    ):
        self._url = url
        self.headers = headers
        self.body = body
        self.service = service

    @property
    @abc.abstractmethod
    def url(self) -> str:
        ...
