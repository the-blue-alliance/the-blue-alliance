from google.appengine.ext.ndb import model
from typing import Any

class _ClassKeyProperty(model.StringProperty):
    def __init__(self, name=..., indexed: bool = ...) -> None: ...

class PolyModel(model.Model):
    class_: Any
