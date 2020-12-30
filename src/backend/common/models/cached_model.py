from typing import Any, Dict, Optional, Set

from google.cloud import ndb


TAffectedReferences = Dict[str, Set[ndb.Key]]


class CachedModel(ndb.Model):
    """
    A base class inheriting from ndb.Model that encapsulates all things needed
    for cache clearing and manipulators
    """

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

    def __init__(self, *args, **kwargs):
        super(CachedModel, self).__init__(*args, **kwargs)

        # The initialization path is different for models vs those created via
        # constructors, so make sure we have a common set of properties defined
        self._fix_up_properties()

    def __setstate__(self, state: Any) -> None:
        """
        TODO this will receive a serialized legacy protobuf,
        we need to implement something similar

        From the legacy NDB model implementation:
        ```
        def __getstate__(self):
            return self._to_pb().Encode()

        def __setstate__(self, serialized_pb):
            pb = entity_pb.EntityProto(serialized_pb)
            self.__init__()
            self.__class__._from_pb(pb, set_key=False, ent=self)
        ```

        See https://github.com/googleapis/python-ndb/issues/587 about fixing upstream
        """
