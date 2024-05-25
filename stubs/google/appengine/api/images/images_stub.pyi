from google.appengine.api import apiproxy_stub as apiproxy_stub, apiproxy_stub_map as apiproxy_stub_map, datastore as datastore, datastore_errors as datastore_errors, images as images
from google.appengine.api.blobstore import blobstore_stub as blobstore_stub
from google.appengine.api.images import images_blob_stub as images_blob_stub, images_service_pb2 as images_service_pb2
from google.appengine.runtime import apiproxy_errors as apiproxy_errors
from typing import Any

BLOB_SERVING_URL_KIND: Any
BMP: str
GIF: str
GS_INFO_KIND: str
ICO: str
JPEG: str
MAX_REQUEST_SIZE: Any
PNG: str
RGB: str
RGBA: str
TIFF: str
WEBP: str
FORMAT_LIST: Any
EXIF_TIME_REGEX: Any

class ImagesServiceStub(apiproxy_stub.APIProxyStub):
    THREADSAFE: bool
    def __init__(self, service_name: str = ..., host_prefix: str = ...) -> None: ...
