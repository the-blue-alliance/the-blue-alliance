from google.appengine.api import api_base_pb2 as api_base_pb2, apiproxy_rpc as apiproxy_rpc, apiproxy_stub as apiproxy_stub, apiproxy_stub_map as apiproxy_stub_map, datastore_types as datastore_types
from google.appengine.datastore import cloud_datastore_validator as cloud_datastore_validator, datastore_pb as datastore_pb, datastore_pbs as datastore_pbs, datastore_query as datastore_query, datastore_stub_util as datastore_stub_util
from google.appengine.datastore.datastore_pbs import googledatastore as googledatastore
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from typing import Any

SERVICE_NAME: str
V3_SERVICE_NAME: str

class _StubIdResolver(datastore_pbs.IdResolver):
    def __init__(self, app_ids: Any | None = ...) -> None: ...
    def resolve_app_id(self, project_id): ...

class CloudDatastoreV1Stub(apiproxy_stub.APIProxyStub):
    THREADSAFE: bool
    def __init__(self, app_id) -> None: ...
