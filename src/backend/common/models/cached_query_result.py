import io
import pickle
import zlib
from typing import Any

from google.appengine.ext import ndb

_ZLIB_COMPRESSION_MARKER = b"x\x9c"


class ImportFixingUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        renamed_module = module
        if module.startswith("models."):
            renamed_module = "backend.common." + module

        return super().find_class(renamed_module, name)


class ImportFixingPickleProperty(ndb.BlobProperty):
    def _to_base_type(self, value: Any) -> bytes:
        """Convert a value to the "base" value type for this property.
        Args:
            value (Any): The value to be converted.
        Returns:
            bytes: The pickled ``value``.
        """

        file_obj = io.BytesIO()
        pickle.Pickler(file_obj, protocol=2, fix_imports=True).dump(value)
        return file_obj.getvalue()

    def _from_base_type(self, value: bytes) -> Any:
        """Convert a value from the "base" value type for this property.
        Args:
            value (bytes): The value to be converted.
        Returns:
            Any: The unpickled ``value``.
        """

        if getattr(self, "_compressed", False) and not isinstance(
            value, ndb.model._CompressedValue
        ):
            if value.startswith(_ZLIB_COMPRESSION_MARKER):
                value = zlib.decompress(value)

        file_obj = io.BytesIO(value)
        return ImportFixingUnpickler(
            file_obj, encoding="bytes", fix_imports=True
        ).load()


class CachedQueryResult(ndb.Model):
    """
    A CachedQueryResult stores the result of an NDB query
    """

    # Only one of result or result_dict should ever be populated for one model
    result = ImportFixingPickleProperty(compressed=True)  # Raw models
    result_dict = ndb.JsonProperty()  # Dict version of models

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
