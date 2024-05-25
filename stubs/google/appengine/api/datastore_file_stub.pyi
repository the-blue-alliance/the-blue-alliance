from google.appengine.api import apiproxy_stub as apiproxy_stub, cmp_compat as cmp_compat, datastore as datastore, datastore_types as datastore_types
from google.appengine.datastore import datastore_pb as datastore_pb, datastore_stub_util as datastore_stub_util
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from google.protobuf import message as message
from typing import Any

logger: Any
long = int

class _StoredEntity:
    record: Any
    encoded_protobuf: Any
    def __init__(self, record) -> None: ...

class KindPseudoKind:
    name: str
    def Query(self, query, filters, orders): ...

class PropertyPseudoKind:
    name: str
    def Query(self, query, filters, orders): ...

class NamespacePseudoKind:
    name: str
    def Query(self, query, filters, orders): ...

class DatastoreFileStub(datastore_stub_util.BaseDatastore, apiproxy_stub.APIProxyStub, datastore_stub_util.DatastoreStub):
    def __init__(self, app_id, datastore_file, history_file: Any | None = ..., require_indexes: bool = ..., service_name: str = ..., trusted: bool = ..., consistency_policy: Any | None = ..., save_changes: bool = ..., root_path: Any | None = ..., use_atexit: bool = ..., auto_id_policy=...) -> None: ...
    def Clear(self) -> None: ...
    READ_PB_EXCEPTIONS: Any
    READ_ERROR_MSG: str
    READ_PY250_MSG: str
    def Read(self) -> None: ...
    def Write(self) -> None: ...
    def MakeSyncCall(self, service, call, request, response, request_id: Any | None = ...) -> None: ...
    def assertPbIsInitialized(self, pb) -> None: ...
