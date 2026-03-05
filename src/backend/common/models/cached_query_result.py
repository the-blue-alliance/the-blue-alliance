import io
import logging
import pickle
import traceback
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

    def _validate_result_properties(self) -> None:
        """
        Validates that all required properties on models in the result field are set.
        Logs an error with stack trace and model key if validation fails.
        """
        if self.result is None:
            return

        # Handle both single model and list of models
        models_to_check = []
        if isinstance(self.result, list):
            models_to_check = self.result
        else:
            models_to_check = [self.result]

        for model in models_to_check:
            # Skip non-CachedModel objects and models without _properties
            if not hasattr(model, "_properties"):
                continue

            missing_properties = []
            for prop_name, prop in model._properties.items():
                # Check if property is required and value is None
                if hasattr(prop, "_required") and prop._required:
                    value = getattr(model, prop_name, None)
                    if value is None:
                        missing_properties.append(prop_name)

            # Log error if any required properties are missing
            if missing_properties:
                stack_trace = "".join(traceback.format_stack())
                model_key = (
                    model.key.urlsafe() if model.key else "No key (unsaved model)"
                )
                cached_result_key = (
                    self.key.urlsafe() if self.key else "No key (unsaved result)"
                )
                logging.error(
                    f"Required properties not set on {model.__class__.__name__} "
                    f"in CachedQueryResult: {', '.join(missing_properties)}\n"
                    f"Model key: {model_key}\n"
                    f"CachedQueryResult key: {cached_result_key}\n"
                    f"Stack trace:\n{stack_trace}"
                )

    def _pre_put_hook(self) -> None:
        """
        Hook called before the entity is written to the datastore.
        Validates all required properties on models in the result field.
        """
        # Only validate if this is a CachedQueryResult instance with the method
        if hasattr(self, "_validate_result_properties"):
            self._validate_result_properties()

    @classmethod
    def _post_get_hook(cls, key: ndb.Key, future: Any) -> None:
        """
        Hook called after the entity is retrieved from the datastore.
        Validates all required properties on models in the result field.
        """
        entity = future.get_result()
        if entity and hasattr(entity, "_validate_result_properties"):
            entity._validate_result_properties()
