from google.appengine.api import apiproxy_stub_map as apiproxy_stub_map, datastore_file_stub as datastore_file_stub, full_app_id as full_app_id
from google.appengine.api.blobstore import blobstore_stub as blobstore_stub, file_blob_storage as file_blob_storage
from google.appengine.api.taskqueue import taskqueue_stub as taskqueue_stub
from google.appengine.datastore import cloud_datastore_v1_remote_stub as cloud_datastore_v1_remote_stub, cloud_datastore_v1_stub as cloud_datastore_v1_stub, datastore_pbs as datastore_pbs, datastore_v4_stub as datastore_v4_stub
from typing import Any

FLAGS: Any

class APITest:
    def ResetApiProxyStubMap(self, force: bool = ...) -> None: ...
    datastore_file: Any
    datastore_history_file: Any
    datastore_stub: Any
    datastore_v4_stub: Any
    cloud_datastore_v1_stub: Any
    def ConfigureDatastore(self, app_id: str = ..., **kwargs) -> None: ...
    blobstore_stub: Any
    def ConfigureBlobstore(self, app_id: str = ...) -> None: ...
    taskqueue_stub: Any
    def ConfigureTaskQueue(self, root_path: Any | None = ...) -> None: ...
