from google.cloud.ndb import model
from typing import Any

class _ClassKeyProperty(model.StringProperty):
    def __init__(self, name: Any = ..., indexed: bool = ...) -> None: ...

class PolyModel(model.Model):
    class_: Any = ...
