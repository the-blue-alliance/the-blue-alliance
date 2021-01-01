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

import array
import struct


class ProtocolBufferEncodeError(Exception):
    pass


TYPE_DOUBLE = 1
TYPE_FLOAT = 2
TYPE_INT64 = 3
TYPE_UINT64 = 4
TYPE_INT32 = 5
TYPE_FIXED64 = 6
TYPE_FIXED32 = 7
TYPE_BOOL = 8
TYPE_STRING = 9
TYPE_GROUP = 10
TYPE_FOREIGN = 11


class Encoder:

    """
    This is a copy of the protobuf encoder from the legacy GAE Runtime
    It has been modified to be python3 compatible and to integrate with the
    cloud NDB library

    Original source from:
    https://github.com/GoogleCloudPlatform/python-compat-runtime/blob/master/appengine-compat/exported_appengine_sdk/google/net/proto/ProtocolBuffer.py#L473
    """

    NUMERIC = 0
    DOUBLE = 1
    STRING = 2
    STARTGROUP = 3
    ENDGROUP = 4
    FLOAT = 5
    MAX_TYPE = 6

    def __init__(self):
        self.buf = array.array("B")
        return

    def buffer(self):
        return self.buf

    def put8(self, v):
        if v < 0 or v >= (1 << 8):
            raise ProtocolBufferEncodeError("u8 too big")
        self.buf.append(v & 255)
        return

    def put16(self, v):
        if v < 0 or v >= (1 << 16):
            raise ProtocolBufferEncodeError("u16 too big")
        self.buf.append((v >> 0) & 255)
        self.buf.append((v >> 8) & 255)
        return

    def put32(self, v):
        if v < 0 or v >= (1 << 32):
            raise ProtocolBufferEncodeError("u32 too big")
        self.buf.append((v >> 0) & 255)
        self.buf.append((v >> 8) & 255)
        self.buf.append((v >> 16) & 255)
        self.buf.append((v >> 24) & 255)
        return

    def put64(self, v):
        if v < 0 or v >= (1 << 64):
            raise ProtocolBufferEncodeError("u64 too big")
        self.buf.append((v >> 0) & 255)
        self.buf.append((v >> 8) & 255)
        self.buf.append((v >> 16) & 255)
        self.buf.append((v >> 24) & 255)
        self.buf.append((v >> 32) & 255)
        self.buf.append((v >> 40) & 255)
        self.buf.append((v >> 48) & 255)
        self.buf.append((v >> 56) & 255)
        return

    def putVarInt32(self, v):

        buf_append = self.buf.append
        if v & 127 == v:
            buf_append(v)
            return
        if v >= 0x80000000 or v < -0x80000000:
            raise ProtocolBufferEncodeError("int32 too big")
        if v < 0:
            v += 0x10000000000000000
        while True:
            bits = v & 127
            v >>= 7
            if v:
                bits |= 128
            buf_append(bits)
            if not v:
                break
        return

    def putVarInt64(self, v):
        buf_append = self.buf.append
        if v >= 0x8000000000000000 or v < -0x8000000000000000:
            raise ProtocolBufferEncodeError("int64 too big")
        if v < 0:
            v += 0x10000000000000000
        while True:
            bits = v & 127
            v >>= 7
            if v:
                bits |= 128
            buf_append(bits)
            if not v:
                break
        return

    def putVarUint64(self, v):
        buf_append = self.buf.append
        if v < 0 or v >= 0x10000000000000000:
            raise ProtocolBufferEncodeError("uint64 too big")
        while True:
            bits = v & 127
            v >>= 7
            if v:
                bits |= 128
            buf_append(bits)
            if not v:
                break
        return

    def putFloat(self, v):
        a = array.array("B")
        a.fromstring(struct.pack("<f", v))
        self.buf.extend(a)
        return

    def putDouble(self, v):
        a = array.array("B")
        a.fromstring(struct.pack("<d", v))
        self.buf.extend(a)
        return

    def putBoolean(self, v):
        if v:
            self.buf.append(1)
        else:
            self.buf.append(0)
        return

    def putPrefixedString(self, v):

        v = str(v)
        self.putVarInt32(len(v))
        self.buf.fromstring(v)
        return

    def putRawString(self, v):
        self.buf.fromstring(v)

    _TYPE_TO_METHOD = {
        TYPE_DOUBLE: putDouble,
        TYPE_FLOAT: putFloat,
        TYPE_FIXED64: put64,
        TYPE_FIXED32: put32,
        TYPE_INT32: putVarInt32,
        TYPE_INT64: putVarInt64,
        TYPE_UINT64: putVarUint64,
        TYPE_BOOL: putBoolean,
        TYPE_STRING: putPrefixedString,
    }

    _TYPE_TO_BYTE_SIZE = {
        TYPE_DOUBLE: 8,
        TYPE_FLOAT: 4,
        TYPE_FIXED64: 8,
        TYPE_FIXED32: 4,
        TYPE_BOOL: 1,
    }
