from typing import Dict, Optional, Set

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

    # This will get updated with the attrs that actually change
    _updated_attrs: Optional[Set[str]] = None

    def __init__(self, *args, **kwargs):
        super(CachedModel, self).__init__(*args, **kwargs)

        # The initialization path is different for models vs those created via
        # constructors, so make sure we have a common set of properties defined
        self._fix_up_properties()
