from typing import Any, Dict, Optional, Set

from google.cloud import ndb
from google.cloud.ndb._legacy_entity_pb import (
    EntityProto,
)

from backend.common.legacy_protobuf.legacy_gae_entity_model_decoder import (
    EntityProtoDecoder,
)
from backend.common.legacy_protobuf.legacy_gae_entity_model_encoder import (
    NdbModelEncoder,
)
from backend.common.legacy_protobuf.legacy_gae_entity_pb_encoder import (
    EntityProtoEncoder,
)
from backend.common.legacy_protobuf.legacy_gae_protobuf import Encoder as ProtoEncoder

TAffectedReferences = Dict[str, Set[Any]]


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

    """
    From the legacy NDB model implementation:
    https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/cf4cab3f1f69cd04e1a9229871be466b53729f3f/ndb/model.py#L2964-L2970

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

    def __getstate__(self) -> bytes:
        pb = NdbModelEncoder.model_to_proto(self)
        encoder = ProtoEncoder()
        EntityProtoEncoder.OutputUnchecked(pb, encoder)
        b = encoder.buffer().tobytes()
        return b

    def __setstate__(self, state: Any) -> None:
        pb = EntityProto()
        pb.MergePartialFromString(state)

        self.__init__()
        EntityProtoDecoder.decode_protobuf(self, pb)
