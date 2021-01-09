#
# Copyright 2008 The ndb Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import datetime
from typing import Any

from google.cloud import ndb
from google.cloud.datastore.helpers import GeoPoint
from google.cloud.ndb._datastore_types import BlobKey
from google.cloud.ndb._legacy_entity_pb import (
    EntityProto,
    Property as ProtoProperty,
    PropertyValue as ProtoPropertyValue,
)
from google.cloud.ndb.model import _BaseValue, _CompressedValue

from backend.common.legacy_protobuf.legacy_gae_entity_model_encoder import (
    EPOCH,
    MEANING_URI_COMPRESSED,
)


class EntityProtoDecoder:
    """
    This is a class that takes fields defined on an EntityProto and sets them on an ndb Model

    This is how we deserialize a protobuf byte string, and get a fully populated model back

    See:
    https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py
    """

    @classmethod
    def decode_protobuf(cls, model: ndb.Model, pb: EntityProto) -> None:
        deserialized_props = {}
        if pb.key().path().element_list():
            key_ref = pb.key()
            app = key_ref.app().decode()
            namespace = key_ref.name_space() if key_ref.has_name_space() else None
            pairs = [
                (elem.type().decode(), elem.id() or elem.name().decode())
                for elem in key_ref.path().element_list()
            ]
            deserialized_props["key"] = ndb.Key(
                pairs=pairs, app=app, namespace=namespace
            )

        def maybe_base_value_or_none(value):
            if isinstance(value, ndb.Key):
                return value
            return None if value is None else _BaseValue(value)

        for pb_prop in pb.property_list():
            prop_name = pb_prop.name().decode()

            # There are some fields we did not port to py3, skip them
            # StructuredProperty uses "." in field names, so skip those
            if not hasattr(model, prop_name) and "." not in prop_name:
                continue

            prop_value = cls._get_prop_value(pb_prop.value(), pb_prop)
            if not hasattr(model, prop_name) and "." in prop_name:
                supername, subname = prop_name.split(".", 1)
                structprop = getattr(model.__class__, supername, None)
                prop_type = structprop._model_class
                if getattr(model, supername) is None:
                    model._set_attributes({supername: prop_type()})
                getattr(model, supername)._set_attributes(
                    {subname: maybe_base_value_or_none(prop_value)}
                )

                if pb_prop.multiple():
                    raise Exception("TODO multiple structured property")

                continue

            if pb_prop.multiple() and not isinstance(prop_value, list):
                prop_value = [maybe_base_value_or_none(prop_value)]
            else:
                prop_value = maybe_base_value_or_none(prop_value)

            deserialized_props[prop_name] = prop_value

        model._set_attributes(deserialized_props)

    @staticmethod
    def _get_prop_value(v: ProtoPropertyValue, p: ProtoProperty) -> Any:
        # rougly based on https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/cf4cab3f1f69cd04e1a9229871be466b53729f3f/ndb/model.py#L2647
        if v.has_stringvalue():
            sval = v.stringvalue()
            meaning = p.meaning()

            if meaning == ProtoProperty.BLOBKEY:
                sval = BlobKey(sval)
            elif meaning == ProtoProperty.BLOB:
                if p.meaning_uri() == MEANING_URI_COMPRESSED:
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
                return EPOCH + datetime.timedelta(microseconds=ival)
            return ival
        elif v.has_booleanvalue():
            return bool(v.booleanvalue())
        elif v.has_doublevalue():
            return v.doublevalue()
        elif v.has_referencevalue():
            rv = v.referencevalue()
            app = rv.app().decode()
            namespace = rv.name_space() if rv.has_name_space() else None
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
