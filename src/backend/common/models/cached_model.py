import datetime
from typing import Any, Dict, Optional, Set

from google.cloud import ndb
from google.cloud.datastore.helpers import GeoPoint
from google.cloud.ndb._datastore_types import BlobKey
from google.cloud.ndb._legacy_entity_pb import (
    EntityProto,
    Property as ProtoProperty,
    PropertyValue as ProtoPropertyValue,
)
from google.cloud.ndb.model import _CompressedValue


TAffectedReferences = Dict[str, Set[ndb.Key]]

_EPOCH = datetime.datetime.utcfromtimestamp(0)
_MEANING_URI_COMPRESSED = "ZLIB"


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
        pb = EntityProto()
        pb.MergePartialFromString(state)

        self.__init__()
        self._set_state_from_pb(pb)

    def _set_state_from_pb(self, pb: EntityProto) -> None:
        deserialized_props = {}
        if len(pb.key().path().element_list()):
            key_ref = pb.key()
            app = key_ref.app().decode()
            namespace = key_ref.name_space()
            pairs = [
                (elem.type().decode(), elem.id() or elem.name().decode())
                for elem in key_ref.path().element_list()
            ]
            deserialized_props["key"] = ndb.Key(
                pairs=pairs, app=app, namespace=namespace
            )

        for pb_prop in pb.property_list():
            prop_name = pb_prop.name().decode()

            # There are some fields we did not port to py3, skip them
            # StructuredProperty uses "." in field names, so skip those
            if not hasattr(self, prop_name) and "." not in prop_name:
                continue

            prop_value = self._get_prop_value(pb_prop.value(), pb_prop)
            if not hasattr(self, prop_name) and "." in prop_name:
                supername, subname = prop_name.split(".", 1)
                structprop = getattr(self.__class__, supername, None)
                prop_type = structprop._model_class
                if getattr(self, supername) is None:
                    self._set_attributes({supername: prop_type()})
                getattr(self, supername)._set_attributes({subname: prop_value})

                if pb_prop.multiple():
                    raise Exception("TODO multiple structured property")

                continue

            if pb_prop.multiple() and not isinstance(prop_value, list):
                prop_value = [prop_value]
            deserialized_props[prop_name] = prop_value
        self._set_attributes(deserialized_props)

    @staticmethod
    def _get_prop_value(v: ProtoPropertyValue, p: ProtoProperty) -> Any:
        # rougly based on https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/cf4cab3f1f69cd04e1a9229871be466b53729f3f/ndb/model.py#L2647
        if v.has_stringvalue():
            sval = v.stringvalue()
            meaning = p.meaning()

            if meaning == ProtoProperty.BLOBKEY:
                sval = BlobKey(sval)
            elif meaning == ProtoProperty.BLOB:
                if p.meaning_uri() == _MEANING_URI_COMPRESSED:
                    sval = _CompressedValue(sval)
            elif meaning == ProtoProperty.ENTITY_PROTO:
                raise Exception("ENTITY_PROTO meaning implementation")
            elif meaning != ProtoProperty.BYTESTRING:
                try:
                    sval = sval.decode("ascii")
                    # If this passes, don't return unicode.
                except UnicodeDecodeError:
                    try:
                        sval = str(sval.decode("utf-8"))
                    except UnicodeDecodeError:
                        pass
            return sval
        elif v.has_int64value():
            ival = v.int64value()
            if p.meaning() == ProtoProperty.GD_WHEN:
                return _EPOCH + datetime.timedelta(microseconds=ival)
            return ival
        elif v.has_booleanvalue():
            return bool(v.booleanvalue())
        elif v.has_doublevalue():
            return v.doublevalue()
        elif v.has_referencevalue():
            rv = v.referencevalue()
            app = rv.app().decode()
            namespace = rv.name_space()
            pairs = [
                (elem.type().decode(), elem.id() or elem.name().decode())
                for elem in rv.pathelement_list()
            ]
            return ndb.Key(pairs=pairs, app=app, namespace=namespace)
        elif v.has_pointvalue():
            pv = v.pointvalue()
            return GeoPoint(pv.x(), pv.y())
        else:
            # A missing value implies null.
            return None
