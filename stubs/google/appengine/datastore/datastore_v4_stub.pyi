from google.appengine.api import api_base_pb2 as api_base_pb2, apiproxy_stub as apiproxy_stub, apiproxy_stub_map as apiproxy_stub_map
from google.appengine.datastore import datastore_pb as datastore_pb, datastore_pbs as datastore_pbs, datastore_query as datastore_query, datastore_stub_util as datastore_stub_util, datastore_v4_pb2 as datastore_v4_pb2, datastore_v4_validator as datastore_v4_validator
from google.appengine.runtime import apiproxy_errors as apiproxy_errors

SERVICE_NAME: str
V3_SERVICE_NAME: str

class DatastoreV4Stub(apiproxy_stub.APIProxyStub):
    THREADSAFE: bool
    def __init__(self, app_id) -> None: ...
