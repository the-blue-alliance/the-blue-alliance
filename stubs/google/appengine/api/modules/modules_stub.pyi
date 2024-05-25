from google.appengine.api import apiproxy_stub as apiproxy_stub, request_info as request_info
from google.appengine.api.modules import modules_service_pb2 as modules_service_pb2
from google.appengine.runtime import apiproxy_errors as apiproxy_errors

class ModulesServiceStub(apiproxy_stub.APIProxyStub):
    THREADSAFE: bool
    def __init__(self, request_data) -> None: ...
