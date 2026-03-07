import logging
import traceback
from typing import Any, Dict, List, Optional, Set

from google.appengine.ext import ndb

TAffectedReferences = Dict[str, Set[Any]]


class CachedModel(ndb.Model):
    """
    A base class inheriting from ndb.Model that encapsulates all things needed
    for cache clearing and manipulators
    """

    # Manually overwritten attributes that shoudln't be updated via automated processes (e.g. via FRC API).
    manual_attrs = ndb.TextProperty(repeated=True)

    # This is set when the model is determined to need updating in ndb
    _dirty: bool = False

    # This is used in post-update hooks to know when a modely was newly created (vs updated)
    _is_new: bool = False

    # This stores a mapping of an model property name --> affected keys for cache clearing
    _affected_references: TAffectedReferences = {}

    # Which references get overwritten
    _mutable_attrs: Set[str] = set()

    # Attributes where overwriting None is allowed
    _allow_none_attrs: Set[str] = set()

    # We will merge the lists of these attrs
    _list_attrs: Set[str] = set()

    _json_attrs: Set[str] = set()

    _auto_union_attrs: Set[str] = set()

    # This will get updated with the attrs that actually change
    _updated_attrs: Optional[Set[str]] = None

    def _validate_required_properties(self) -> bool:
        """
        Validates that all required properties on the model are set.
        Logs an error with stack trace and model key if validation fails.

        Returns True when one or more required properties are missing,
        otherwise False.
        """
        # Skip validation if model doesn't have _properties attribute
        if not hasattr(self, "_properties"):
            return False

        missing_properties: List[str] = []

        # Iterate through all properties and check if required ones are set
        # pyre-ignore[16]: _properties is an NDB internal attribute
        for prop_name, prop in self._properties.items():
            # Check if property is required and value is None
            if hasattr(prop, "_required") and prop._required:
                value = getattr(self, prop_name, None)
                if value is None:
                    missing_properties.append(prop_name)

        # Log error if any required properties are missing
        if missing_properties:
            stack_trace = "".join(traceback.format_stack())
            model_key = self.key.urlsafe() if self.key else "No key (unsaved model)"
            logging.error(
                f"Required properties not set on {self.__class__.__name__}: "
                f"{', '.join(missing_properties)}\n"
                f"Model key: {model_key}\n"
                f"Stack trace:\n{stack_trace}"
            )
            return True

        return False

    def _pre_put_hook(self) -> None:
        """
        Hook called before the entity is written to the datastore.
        Raises BadValueError if any required properties are missing.
        """
        if not hasattr(self, "_properties"):
            return

        missing_properties: List[str] = []
        # pyre-ignore[16]: _properties is an NDB internal attribute
        for prop_name, prop in self._properties.items():
            if hasattr(prop, "_required") and prop._required:
                value = getattr(self, prop_name, None)
                if value is None:
                    missing_properties.append(prop_name)

        if missing_properties:
            from google.appengine.api import datastore_errors

            model_key = self.key.urlsafe() if self.key else "No key (unsaved model)"
            raise datastore_errors.BadValueError(
                f"Required properties not set on {self.__class__.__name__} "
                f"(key: {model_key}): {', '.join(missing_properties)}"
            )

    @classmethod
    def _post_get_hook(cls, key: ndb.Key, future: Any) -> None:
        """
        Hook called after the entity is retrieved from the datastore.
        Validates all required properties are set on the retrieved entity.
        """
        entity = future.get_result()
        # Check if the method exists before calling. NDB's hook system can invoke
        # this on different model types (especially when tests manipulate NDB's kind map).
        if entity and hasattr(entity, "_validate_required_properties"):
            entity._validate_required_properties()
