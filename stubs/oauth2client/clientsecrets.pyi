from typing import Any, Optional

TYPE_WEB: str
TYPE_INSTALLED: str
VALID_CLIENT: Any

class Error(Exception): ...
class InvalidClientSecretsError(Error): ...

def load(fp: Any): ...
def loads(s: Any): ...
def loadfile(filename: Any, cache: Optional[Any] = ...): ...
