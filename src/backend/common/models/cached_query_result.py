import pickle
from typing import Any

from google.appengine.ext import ndb


class PickleProperty(ndb.BlobProperty):
    def _to_base_type(self, value: Any) -> bytes:
        return pickle.dumps(value, protocol=5)

    def _from_base_type(self, value: bytes) -> Any:
        return pickle.loads(value)


class CachedQueryResult(ndb.Model):
    """
    A CachedQueryResult stores the result of an NDB query
    """

    # Only one of result or result_dict should ever be populated for one model
    result = PickleProperty(compressed=True)  # Raw models
    result_dict = ndb.JsonProperty()  # Dict version of models

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
