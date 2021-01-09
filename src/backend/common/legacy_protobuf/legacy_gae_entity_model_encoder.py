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
from typing import Any, Optional

from google.cloud import datastore
from google.cloud import ndb
from google.cloud.datastore.helpers import GeoPoint
from google.cloud.ndb._datastore_types import BlobKey
from google.cloud.ndb._legacy_entity_pb import (
    EntityProto,
    Property,
    PropertyValue,
)


EPOCH = datetime.datetime.utcfromtimestamp(0)
MEANING_URI_COMPRESSED = "ZLIB"
MAX_INT = 0x7FFFFFFFFFFFFFFF  # 2 ** 63 - 1


class NdbModelEncoder:
    """
    This class implements the legacy _db_set_value functions for the various property types
    See instances of that method in:
    https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py
    """

    @classmethod
    def model_to_proto(cls, model: ndb.Model) -> EntityProto:
        pb = EntityProto()
        cls._add_key_to_entityproto(model, pb)

        for name, prop in model._properties.items():  # pyre-ignore[16]
            values = prop._get_base_value_unwrapped_as_list(model)
            for val in values:
                NdbModelEncoder.copy_property_to_proto(pb, prop, val)
        return pb

    @classmethod
    def copy_property_to_proto(
        cls,
        pb: EntityProto,
        prop: Any,
        val: Optional[Any],
        prop_prefix: str = "",
    ) -> None:
        if isinstance(prop, ndb.StructuredProperty):
            cls._copy_structured_property_to_proto(prop, pb, val, prop_prefix)
            return

        p = pb.add_property()
        p.set_name(prop_prefix + prop._name)  # pyre-ignore[6]
        p.set_multiple(prop._repeated)
        v = p.mutable_value()

        if val is None:
            return

        if isinstance(prop, ndb.BooleanProperty):
            cls._copy_boolean_property_to_proto(prop, v, p, val)
        elif isinstance(prop, ndb.IntegerProperty):
            cls._copy_integer_property_to_proto(prop, v, p, val)
        elif isinstance(prop, ndb.FloatProperty):
            cls._copy_float_property_to_proto(prop, v, p, val)
        elif isinstance(prop, ndb.BlobProperty):
            cls._copy_blob_property_to_proto(prop, v, p, val)
        elif isinstance(prop, ndb.TextProperty):
            cls._copy_text_property_to_proto(prop, v, p, val)
        elif isinstance(prop, ndb.GeoPtProperty):
            cls._copy_geo_pt_property_to_proto(prop, v, p, val)
        elif isinstance(prop, ndb.KeyProperty):
            cls._copy_key_property_to_proto(prop, v, p, val)
        elif isinstance(prop, ndb.BlobKeyProperty):
            cls._copy_blob_key_property_to_proto(prop, v, p, val)
        elif isinstance(prop, ndb.DateTimeProperty):
            cls._copy_date_time_property_to_proto(prop, v, p, val)
        elif isinstance(prop, ndb.GenericProperty):
            cls._copy_generic_property_to_proto(prop, v, p, val)
        else:
            raise NotImplementedError(f"{prop}")

    @staticmethod
    def _add_key_to_entityproto(model: ndb.Model, pb: EntityProto) -> None:
        """Internal helper to copy the key into a protobuf."""
        ref = model.key.reference()

        pb_key = pb.mutable_key()
        pb_key.set_app(ref.app)
        if ref.HasField("name_space"):
            pb_key.set_name_space(ref.name_space)
        pb_key_path = pb_key.mutable_path()
        for path_element in ref.path.element:
            e = pb_key_path.add_element()
            e.set_type(path_element.type)
            if path_element.HasField("id"):
                e.set_id(path_element.id)
            elif path_element.HasField("name"):
                e.set_name(path_element.name)
        if ref.HasField("database_id"):
            pb_key.set_database_id(ref.database_id)

    @staticmethod
    def _copy_boolean_property_to_proto(
        self: ndb.BooleanProperty, v: PropertyValue, _p: Property, value: Any
    ) -> None:
        # From BooleanProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L1599
        if not isinstance(value, bool):
            raise TypeError(
                "BooleanProperty %s can only be set to bool values; received %r"
                % (self._name, value)
            )
        v.set_booleanvalue(value)

    @staticmethod
    def _copy_integer_property_to_proto(
        self: ndb.IntegerProperty, v: PropertyValue, _p: Property, value: Any
    ) -> None:
        # From IntegerProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L1622
        if not isinstance(value, (bool, int)):
            raise TypeError(
                "IntegerProperty %s can only be set to integer values; "
                "received %r" % (self._name, value)
            )
        v.set_int64value(value)

    @staticmethod
    def _copy_float_property_to_proto(
        self: ndb.FloatProperty, v: PropertyValue, _p: Property, value: Any
    ) -> None:
        # From FloatProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L1646
        if not isinstance(value, (bool, int, float)):
            raise TypeError(
                "FloatProperty %s can only be set to integer or float "
                "values; received %r" % (self._name, value)
            )
        v.set_doublevalue(float(value))

    @staticmethod
    def _copy_blob_property_to_proto(
        self: ndb.BlobProperty, v: PropertyValue, p: Property, value: Any
    ) -> None:
        # From BlobProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L1735
        if isinstance(value, ndb.model._CompressedValue):
            # Use meaning_uri because setting meaning to something else that is not
            # BLOB or BYTESTRING will cause the value to be decoded from utf-8 in
            # datastore_types.FromPropertyPb. That would break the compressed string.
            p.set_meaning_uri(MEANING_URI_COMPRESSED.encode())
            p.set_meaning(Property.BLOB)
            value = value.z_val
        else:
            if self._indexed:
                p.set_meaning(Property.BYTESTRING)
            else:
                p.set_meaning(Property.BLOB)
        v.set_stringvalue(value)

    @staticmethod
    def _copy_text_property_to_proto(
        self: ndb.TextProperty, v: PropertyValue, p: Property, value: Any
    ) -> None:
        # TextProperty does not inherit from BlobProperty in cloud-ndb, so copy the implementation here
        # From BlobProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L1735
        if isinstance(value, ndb.model._CompressedValue):
            # Use meaning_uri because setting meaning to something else that is not
            # BLOB or BYTESTRING will cause the value to be decoded from utf-8 in
            # datastore_types.FromPropertyPb. That would break the compressed string.
            p.set_meaning_uri(MEANING_URI_COMPRESSED.encode())
            p.set_meaning(Property.BLOB)
            value = value.z_val
        else:
            # TextProperty can never be indexed
            p.set_meaning(Property.TEXT)
        v.set_stringvalue(value)

    @staticmethod
    def _copy_geo_pt_property_to_proto(
        self: ndb.GeoPtProperty, v: PropertyValue, p: Property, value: Any
    ) -> None:
        # From GeoPtProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L1822
        if not isinstance(value, GeoPoint):
            raise TypeError(
                "GeoPtProperty %s can only be set to GeoPt values; "
                "received %r" % (self._name, value)
            )
        p.set_meaning(Property.GEORSS_POINT)
        pv = v.mutable_pointvalue()
        pv.set_x(value.latitude)
        pv.set_y(value.longitude)

    @staticmethod
    def _copy_key_property_to_proto(
        self: ndb.KeyProperty, v: PropertyValue, p: Property, value: Any
    ) -> None:
        # From KeyProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L2023
        if not isinstance(value, datastore.Key):
            raise TypeError(
                "KeyProperty %s can only be set to Key values; "
                "received %r" % (self._name, value)
            )
        rv = v.mutable_referencevalue()  # A Reference
        rv.set_app(value.project)
        if value.namespace:
            rv.set_name_space(value.namespace)
        for elem in datastore.key._to_legacy_path(value._path).element:  # pyre-ignore
            e = rv.add_pathelement()
            e.set_type(elem.type)
            if elem.HasField("id"):
                e.set_id(elem.id)
            elif elem.HasField("name"):
                e.set_name(elem.name)

    @staticmethod
    def _copy_blob_key_property_to_proto(
        self: ndb.BlobKeyProperty, v: PropertyValue, p: Property, value: Any
    ) -> None:
        # From BlobKeyProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L2059
        if not isinstance(value, BlobKey):
            raise TypeError(
                "BlobKeyProperty %s can only be set to BlobKey values; "
                "received %r" % (self._name, value)
            )
        p.set_meaning(Property.BLOBKEY)
        v.set_stringvalue(str(value).encode())

    @staticmethod
    def _copy_date_time_property_to_proto(
        self: ndb.DateTimeProperty, v: PropertyValue, p: Property, value: Any
    ) -> None:
        # From DateTimeProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L2122
        if not isinstance(value, datetime.datetime):
            raise TypeError(
                "DatetimeProperty %s can only be set to datetime values; "
                "received %r" % (self._name, value)
            )
        if value.tzinfo is not None:
            raise NotImplementedError(
                "DatetimeProperty %s can only support UTC. "
                "Please derive a new Property to support "
                "alternative timezones." % self._name
            )
        dt = value - EPOCH
        ival = dt.microseconds + 1000000 * (dt.seconds + 24 * 3600 * dt.days)
        v.set_int64value(ival)
        p.set_meaning(Property.GD_WHEN)

    @staticmethod
    def _copy_generic_property_to_proto(
        self: ndb.GenericProperty, v: PropertyValue, p: Property, value: Any
    ) -> None:
        # From GenericProperty._db_set_value
        # https://github.com/GoogleCloudPlatform/datastore-ndb-python/blob/master/ndb/model.py#L2706
        # TODO: use a dict mapping types to functions
        if isinstance(value, bytes):
            v.set_stringvalue(value)
            # TODO: Set meaning to BLOB or BYTESTRING if it's not UTF-8?
            # (Or TEXT if unindexed.)
        elif isinstance(value, str):
            v.set_stringvalue(value.encode("utf8"))
            if not self._indexed:
                p.set_meaning(Property.TEXT)
        elif isinstance(value, bool):  # Must test before int!
            v.set_booleanvalue(value)
        elif isinstance(value, int):
            if not (-MAX_INT <= value < MAX_INT):
                raise TypeError(
                    "Property %s can only accept 64-bit integers; "
                    "received %s" % (self._name, value)
                )
            v.set_int64value(value)
        elif isinstance(value, float):
            v.set_doublevalue(value)
        elif isinstance(value, ndb.Key):
            # See datastore_types.PackKey
            ref = value.reference()
            rv = v.mutable_referencevalue()  # A Reference
            rv.set_app(ref.app())
            if ref.has_name_space():
                rv.set_name_space(ref.name_space())
            for elem in ref.path().element_list():
                e = rv.add_pathelement()
                e.set_type(elem.type())
                if elem.id is not None:
                    e.set_id(elem.id)
                elif elem.name is not None:
                    e.set_name(elem.name)
        elif isinstance(value, datetime.datetime):
            if value.tzinfo is not None:
                raise NotImplementedError(
                    "Property %s can only support the UTC. "
                    "Please derive a new Property to support "
                    "alternative timezones." % self._name
                )
            dt = value - EPOCH
            ival = dt.microseconds + 1000000 * (dt.seconds + 24 * 3600 * dt.days)
            v.set_int64value(ival)
            p.set_meaning(Property.GD_WHEN)
        elif isinstance(value, GeoPoint):
            p.set_meaning(Property.GEORSS_POINT)
            pv = v.mutable_pointvalue()
            pv.set_x(value.latitude)
            pv.set_y(value.longitude)
        elif isinstance(value, BlobKey):
            v.set_stringvalue(str(value).encode())
            p.set_meaning(Property.BLOBKEY)
        elif isinstance(value, ndb.Model):
            """
            TODO
            set_key = value.key is not None
            pb = value._to_pb(set_key=set_key)
            value = pb.SerializePartialToString()
            v.set_stringvalue(value)
            p.set_meaning(Property.ENTITY_PROTO)
            """
        elif isinstance(value, ndb.model._CompressedValue):
            value = value.z_val
            v.set_stringvalue(value)
            p.set_meaning_uri(MEANING_URI_COMPRESSED.encode())
            p.set_meaning(Property.BLOB)
        else:
            raise NotImplementedError(
                "Property %s does not support %s types." % (self._name, type(value))
            )

    @classmethod
    def _copy_structured_property_to_proto(
        cls, self: ndb.StructuredProperty, pb: EntityProto, value: Any, prop_prefix: str
    ) -> None:
        value_type = self._model_class
        if value is not None:
            # TODO: Avoid re-sorting for repeated values.
            for name, prop in sorted(value.items()):
                cls.copy_property_to_proto(
                    pb, getattr(value_type, name), prop, self._name + "."
                )
        else:
            # Serialize a single None
            p = pb.add_property()
            p.set_name(prop_prefix + self._name)  # pyre-ignore[6]
            p.set_multiple(self._repeated)
            p.mutable_value()
