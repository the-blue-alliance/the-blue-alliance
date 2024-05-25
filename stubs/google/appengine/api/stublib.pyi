import abc

class Stub(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def patchers(self): ...

class Patchers(list):
    def StartAll(self): ...
    def StopAll(self) -> None: ...
