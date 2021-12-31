from google.appengine.api import request_info as request_info
from typing import Any

class NotSupportedError(request_info.Error): ...

class LocalDispatcher(request_info.Dispatcher):
    def __init__(self, default_hostname: Any | None = ..., app: Any | None = ...) -> None: ...
    def get_module_names(self): ...
    def get_versions(self, module): ...
    def get_default_version(self, module): ...
    def get_hostname(self, module, version, instance: Any | None = ...): ...
    def set_num_instances(self, module, version, instances) -> None: ...
    def get_num_instances(self, module, version) -> None: ...
    def start_version(self, module, version) -> None: ...
    def stop_version(self, module, version) -> None: ...
    def add_event(self, runnable, eta, service: Any | None = ..., event_id: Any | None = ...) -> None: ...
    def update_event(self, eta, service, event_id) -> None: ...
    def add_request(self, method, relative_url, headers, body, source_ip, module_name: Any | None = ..., version: Any | None = ..., instance_id: Any | None = ...): ...
    def add_async_request(self, method, relative_url, headers, body, source_ip, module_name: Any | None = ..., version: Any | None = ..., instance_id: Any | None = ...) -> None: ...
    def send_background_request(self, module_name, version, instance, background_request_id) -> None: ...

class LocalRequestInfo(request_info._LocalRequestInfo):
    def __init__(self, default_address: Any | None = ..., app: Any | None = ...) -> None: ...
    def get_dispatcher(self): ...
    def get_address(self): ...
