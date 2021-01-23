import io
import pickle

from google.appengine.ext import ndb


class ImportFixingUnpickler(pickle.Unpickler):
    """
    In the case where we're reading a CachedQueryResult written by
    the py3 version of TBA, we'll need to fix the imports to be
    compatible with this one.
    """

    def find_class(self, module, name):
        renamed_module = module
        prefix = "backend.common."
        if module.startswith(prefix):
            renamed_module = module[len(prefix):]

        return pickle.Unpickler.find_class(self, renamed_module, name)


class ImportFixingPickleProperty(ndb.BlobProperty):
    def _to_base_type(self, value):
        """Convert a value to the "base" value type for this property.
        Args:
            value (Any): The value to be converted.
        Returns:
            bytes: The pickled ``value``.
        """

        file_obj = io.BytesIO()
        pickle.Pickler(file_obj, protocol=2).dump(value)
        return file_obj.getvalue()

    def _from_base_type(self, value):
        """Convert a value from the "base" value type for this property.
        Args:
            value (bytes): The value to be converted.
        Returns:
            Any: The unpickled ``value``.
        """

        file_obj = io.BytesIO(value)
        return ImportFixingUnpickler(file_obj).load()


class CachedQueryResult(ndb.Model):
    """
    A CachedQueryResult stores the result of an NDB query
    """
    # Only one of result or result_dict should ever be populated for one model
    result = ImportFixingPickleProperty(compressed=True)  # Raw models
    result_dict = ndb.JsonProperty()  # Dict version of models

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
