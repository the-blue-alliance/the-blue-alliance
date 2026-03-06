import io
import logging
import pickle
import traceback
import zlib
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
        Raises BadValueError if any required properties are missing in cached models.
        """
        if self.result is None:
            return

        from google.appengine.api import datastore_errors

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

            # Raise exception if any required properties are missing
            if missing_properties:
                model_key = (
                    model.key.urlsafe() if model.key else "No key (unsaved model)"
                )
                cached_result_key = (
                    self.key.urlsafe() if self.key else "No key (unsaved result)"
                )
                raise datastore_errors.BadValueError(
                    f"Required properties not set on {model.__class__.__name__} "
                    f"in CachedQueryResult (model key: {model_key}, "
                    f"result key: {cached_result_key}): "
                    f"{', '.join(missing_properties)}"
                )

    @classmethod
    def _post_get_hook(cls, key: ndb.Key, future: Any) -> None:
        """
        Hook called after the entity is retrieved from the datastore.
        Validates all required properties on models in the result field.
        """
        entity = future.get_result()
        # Check if the method exists before calling. NDB's hook system can invoke
        # this on different model types (especially when tests manipulate NDB's kind map).
        if entity and hasattr(entity, "_validate_result_properties"):
            entity._validate_result_properties()
