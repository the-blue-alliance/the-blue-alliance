#
# Copyright 2007 Google Inc.
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
#

from typing import Any, cast

from google.cloud.ndb._legacy_entity_pb import (
    EntityProto,
    Path,
    Path_Element,
    Property,
    PropertyValue,
    PropertyValue_PointValue,
    PropertyValue_ReferenceValue,
    PropertyValue_ReferenceValuePathElement,
    Reference,
)

from backend.common.legacy_protobuf.legacy_gae_protobuf import Encoder


class EntityProtoEncoder:
    """
    This is a class that implements OutputUnchecked() for legacy entity_pb types
    Normally, this is a method defined on ProtocolMessage classes,
    but until this ability exists in the upstream library, we'll handle it separately

    These serialization funcations are based on the original implementations of
    OutputUnchecked, but modified to use the cloud ndb library's types and ported to py3

    See:
    https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py
    """

    @classmethod
    def OutputUnchecked(cls, obj: Any, out: Encoder) -> None:
        if isinstance(obj, EntityProto):
            cls._encode_entity_proto(obj, out)
        elif isinstance(obj, Reference):
            cls._encode_reference(obj, out)
        elif isinstance(obj, Path):
            cls._encode_path(obj, out)
        elif isinstance(obj, Path_Element):
            cls._encode_path_element(obj, out)
        elif isinstance(obj, Property):
            cls._encode_property(obj, out)
        elif isinstance(obj, PropertyValue):
            cls._encode_property_value(obj, out)
        elif isinstance(obj, PropertyValue_ReferenceValue):
            cls._encode_property_value_reference_value(obj, out)
        elif isinstance(obj, PropertyValue_PointValue):
            cls._encode_property_value_point_value(obj, out)
        elif isinstance(obj, PropertyValue_ReferenceValuePathElement):
            cls._encode_property_value_reference_value_path_element(obj, out)
        else:
            raise NotImplementedError

    @staticmethod
    def _encode_entity_proto(self: EntityProto, out: Encoder) -> None:
        # From EntityProto.OutputUnchecked
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L2508-L2532
        if self.has_kind_:
            out.putVarInt32(32)
            out.putVarInt32(self.kind_)
        if self.has_kind_uri_:
            out.putVarInt32(42)
            out.putPrefixedString(self.kind_uri_)
        out.putVarInt32(106)
        out.putVarInt32(EntityProtoByteSize.ByteSize(self.key_))
        EntityProtoEncoder.OutputUnchecked(self.key_, out)
        for i in range(len(self.property_)):
            out.putVarInt32(114)
            out.putVarInt32(EntityProtoByteSize.ByteSize(self.property_[i]))
            EntityProtoEncoder.OutputUnchecked(self.property_[i], out)
        # Skip encoding raw_property
        # It's not present in cloud-ndb's implementation

        # encode a dummy entity_group - it's not present in cloud ndb
        # but is requird by legacy NDB
        entity_group = Path()
        out.putVarInt32(130)
        out.putVarInt32(EntityProtoByteSize.ByteSize(entity_group))
        EntityProtoEncoder.OutputUnchecked(entity_group, out)

        if self.has_owner_:
            out.putVarInt32(138)
            out.putVarInt32(self.owner_.ByteSize())
            self.owner_.OutputUnchecked(out)

    @staticmethod
    def _encode_reference(self: Reference, out: Encoder) -> None:
        # From Reference.OutputUnchecked
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L1887
        out.putVarInt32(106)
        out.putPrefixedString(self.app_)
        out.putVarInt32(114)
        out.putVarInt32(EntityProtoByteSize.ByteSize(self.path_))
        EntityProtoEncoder.OutputUnchecked(self.path_, out)
        if self.has_name_space_:
            out.putVarInt32(162)
            out.putPrefixedString(self.name_space_)
        if self.has_database_id_:
            out.putVarInt32(186)
            out.putPrefixedString(self.database_id_)

    @staticmethod
    def _encode_path(self: Path, out: Encoder) -> None:
        # From Path.OutputUnchecked
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L1703
        for i in range(len(self.element_)):
            out.putVarInt32(11)
            EntityProtoEncoder.OutputUnchecked(self.element_[i], out)
            out.putVarInt32(12)

    @staticmethod
    def _encode_path_element(self: Path_Element, out: Encoder) -> None:
        # From Path_Element.OutputUnchecked
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L1601
        out.putVarInt32(18)
        out.putPrefixedString(self.type_)
        if self.has_id_:
            out.putVarInt32(24)
            out.putVarInt64(self.id_)
        if self.has_name_:
            out.putVarInt32(34)
            out.putPrefixedString(self.name_)

    @staticmethod
    def _encode_property(self: Property, out: Encoder) -> None:
        # From Property.OutputUnchecked
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L1375
        if self.has_meaning_:
            out.putVarInt32(8)
            out.putVarInt32(self.meaning_)
        if self.has_meaning_uri_:
            out.putVarInt32(18)
            out.putPrefixedString(self.meaning_uri_)
        out.putVarInt32(26)
        out.putPrefixedString(self.name_)
        out.putVarInt32(32)
        out.putBoolean(self.multiple_)
        out.putVarInt32(42)
        out.putVarInt32(EntityProtoByteSize.ByteSize(self.value_))
        EntityProtoEncoder.OutputUnchecked(self.value_, out)
        if self.has_stashed_:
            out.putVarInt32(48)
            out.putVarInt32(self.stashed_)
        if self.has_computed_:
            out.putVarInt32(56)
            out.putBoolean(self.computed_)

    @staticmethod
    def _encode_property_value(self: PropertyValue, out: Encoder) -> None:
        # From PropertyValue.OutputUnchecked
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L950
        if self.has_int64value_:
            out.putVarInt32(8)
            out.putVarInt64(self.int64value_)
        if self.has_booleanvalue_:
            out.putVarInt32(16)
            out.putBoolean(self.booleanvalue_)
        if self.has_stringvalue_:
            out.putVarInt32(26)
            out.putPrefixedString(self.stringvalue_)
        if self.has_doublevalue_:
            out.putVarInt32(33)
            out.putDouble(self.doublevalue_)
        if self.has_pointvalue_:
            out.putVarInt32(43)
            EntityProtoEncoder.OutputUnchecked(self.pointvalue_, out)
            out.putVarInt32(44)
        # Skipping user value, this doesn't exist in py3
        if self.has_referencevalue_:
            out.putVarInt32(99)
            EntityProtoEncoder.OutputUnchecked(self.referencevalue_, out)
            out.putVarInt32(100)

    @staticmethod
    def _encode_property_value_reference_value(
        self: PropertyValue_ReferenceValue, out: Encoder
    ) -> None:
        # From PropertyValue_ReferenceValue.OutputUnchecked
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L688
        out.putVarInt32(106)
        out.putPrefixedString(self.app_)
        for i in range(len(self.pathelement_)):
            out.putVarInt32(115)
            EntityProtoEncoder.OutputUnchecked(self.pathelement_[i], out)
            out.putVarInt32(116)
        if self.has_name_space_:
            out.putVarInt32(162)
            out.putPrefixedString(self.name_space_)
        if self.has_database_id_:
            out.putVarInt32(186)
            out.putPrefixedString(self.database_id_)

    @staticmethod
    def _encode_property_value_point_value(
        self: PropertyValue_PointValue, out: Encoder
    ) -> None:
        # From PropertyValue_PointValue.OutputUnchecked
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L251
        out.putVarInt32(49)
        out.putDouble(self.x_)
        out.putVarInt32(57)
        out.putDouble(self.y_)

    @staticmethod
    def _encode_property_value_reference_value_path_element(
        self: PropertyValue_ReferenceValuePathElement, out: Encoder
    ) -> None:
        # From PropertyValue_ReferenceValuePathElement.OutputUnchecked
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L127
        out.putVarInt32(122)
        out.putPrefixedString(self.type_)
        if self.has_id_:
            out.putVarInt32(128)
            out.putVarInt64(self.id_)
        if self.has_name_:
            out.putVarInt32(138)
            out.putPrefixedString(self.name_)


class EntityProtoByteSize:
    """
    A similar thing as above, but for the ByteSize methods

    These funcations are based on the original implementations of
    ByteSize, but modified to use the cloud ndb library's types and ported to py3

    See:
    https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py
    """

    @classmethod
    def ByteSize(cls, obj: Any) -> int:
        if isinstance(obj, EntityProto):
            return cls._byte_size_entity_proto(obj)
        elif isinstance(obj, Reference):
            return cls._byte_size_reference(obj)
        elif isinstance(obj, Path):
            return cls._byte_size_path(obj)
        elif isinstance(obj, Path_Element):
            return cls._byte_size_path_element(obj)
        elif isinstance(obj, Property):
            return cls._byte_size_property(obj)
        elif isinstance(obj, PropertyValue):
            return cls._byte_size_property_value(obj)
        elif isinstance(obj, PropertyValue_ReferenceValue):
            return cls._byte_size_property_value_reference_value(obj)
        elif isinstance(obj, PropertyValue_PointValue):
            return cls._byte_size_property_value_point_value(obj)
        elif isinstance(obj, PropertyValue_ReferenceValuePathElement):
            return cls._byte_size_property_value_reference_value_path_element(obj)
        else:
            raise NotImplementedError

    @classmethod
    def lengthVarInt32(cls, n: int) -> int:
        return cls.lengthVarInt64(n)

    @classmethod
    def lengthVarInt64(cls, n: int) -> int:
        if n < 0:
            return 10
        result = 0
        while 1:
            result += 1
            n >>= 7
            if n == 0:
                break
        return result

    @classmethod
    def lengthString(cls, n: int) -> int:
        return cls.lengthVarInt32(n) + n

    @staticmethod
    def _byte_size_entity_proto(self: EntityProto) -> int:
        # From EntityProto.ByteSize
        # Not including entity_group or raw_property
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L2469
        n = 0
        n += EntityProtoByteSize.lengthString(EntityProtoByteSize.ByteSize(self.key_))
        if self.has_owner_:
            n += 2 + EntityProtoByteSize.lengthString(self.owner_.ByteSize())
        if self.has_kind_:
            n += 1 + EntityProtoByteSize.lengthVarInt64(self.kind_)
        if self.has_kind_uri_:
            n += 1 + EntityProtoByteSize.lengthString(len(self.kind_uri_))
        n += 1 * len(self.property_)
        for i in range(len(self.property_)):
            n += EntityProtoByteSize.lengthString(
                EntityProtoByteSize.ByteSize(self.property_[i])
            )
        return n + 3

    @staticmethod
    def _byte_size_reference(self: Reference) -> int:
        # From Reference.ByteSize
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L1861
        n = 0
        n += EntityProtoByteSize.lengthString(len(self.app_))
        if self.has_name_space_:
            n += 2 + EntityProtoByteSize.lengthString(len(self.name_space_))
        n += EntityProtoByteSize.lengthString(EntityProtoByteSize.ByteSize(self.path_))
        if self.has_database_id_:
            n += 2 + EntityProtoByteSize.lengthString(len(self.database_id_))
        return n + 2

    @staticmethod
    def _byte_size_path(self: Path) -> int:
        # From Path.ByteSize
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L1688
        n = 0
        n += 2 * len(self.element_)
        for i in range(len(self.element_)):
            n += EntityProtoByteSize.ByteSize(self.element_[i])
        return n

    @staticmethod
    def _byte_size_path_element(self: Path_Element) -> int:
        # From Path_Element.ByteSize
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L1580
        n = 0
        n += EntityProtoByteSize.lengthString(len(self.type_))
        if self.has_id_:
            n += 1 + EntityProtoByteSize.lengthVarInt64(self.id_)
        if self.has_name_:
            n += 1 + EntityProtoByteSize.lengthString(len(self.name_))
        return n + 1

    @staticmethod
    def _byte_size_property(self: Property) -> int:
        # From Property.ByteSize
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L1340
        n = 0
        if self.has_meaning_:
            n += 1 + EntityProtoByteSize.lengthVarInt64(self.meaning_)
        if self.has_meaning_uri_:
            n += 1 + EntityProtoByteSize.lengthString(len(self.meaning_uri_))
        n += EntityProtoByteSize.lengthString(len(self.name_))
        n += EntityProtoByteSize.lengthString(EntityProtoByteSize.ByteSize(self.value_))
        if self.has_stashed_:
            n += 1 + EntityProtoByteSize.lengthVarInt64(self.stashed_)
        if self.has_computed_:
            n += 2
        return n + 4

    @staticmethod
    def _byte_size_property_value(self: PropertyValue) -> int:
        # From PropertyValue.ByteSize
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L919
        n = 0
        if self.has_int64value_:
            n += 1 + EntityProtoByteSize.lengthVarInt64(self.int64value_)
        if self.has_booleanvalue_:
            n += 2
        if self.has_stringvalue_:
            assert isinstance(self.stringvalue_, (str, bytes))
            if isinstance(self.stringvalue_, str):
                str_len = len(cast(str, self.stringvalue_).encode())
            else:
                str_len = len(self.stringvalue_)

            n += 1 + EntityProtoByteSize.lengthString(str_len)
        if self.has_doublevalue_:
            n += 9
        if self.has_pointvalue_:
            n += 2 + EntityProtoByteSize.ByteSize(self.pointvalue_)
        # Skipping uservalue
        if self.has_referencevalue_:
            n += 2 + EntityProtoByteSize.ByteSize(self.referencevalue_)
        return n

    @staticmethod
    def _byte_size_property_value_reference_value(
        self: PropertyValue_ReferenceValue,
    ) -> int:
        # From PropertyValue_ReferenceValue.ByteSize
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L662
        n = 0
        n += EntityProtoByteSize.lengthString(len(self.app_))
        if self.has_name_space_:
            n += 2 + EntityProtoByteSize.lengthString(len(self.name_space_))
        n += 2 * len(self.pathelement_)
        for i in range(len(self.pathelement_)):
            n += EntityProtoByteSize.ByteSize(self.pathelement_[i])
        if self.has_database_id_:
            n += 2 + EntityProtoByteSize.lengthString(len(self.database_id_))
        return n + 1

    @staticmethod
    def _byte_size_property_value_point_value(self: PropertyValue_PointValue) -> int:
        # From PropertyValue_PointValue.ByteSize
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L235
        n = 0
        return n + 18

    @staticmethod
    def _byte_size_property_value_reference_value_path_element(
        self: PropertyValue_ReferenceValuePathElement,
    ) -> int:
        # From PropertyValue_ReferenceValuePathElement.ByteSize
        # https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/appengine/datastore/entity_pb.py#L106
        n = 0
        n += EntityProtoByteSize.lengthString(len(self.type_))
        if self.has_id_:
            n += 2 + EntityProtoByteSize.lengthVarInt64(self.id_)
        if self.has_name_:
            n += 2 + EntityProtoByteSize.lengthString(len(self.name_))
        return n + 1
