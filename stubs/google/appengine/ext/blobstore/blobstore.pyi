from google.appengine.api.blobstore import blobstore
from google.appengine.ext import db
from typing import Any

Error = blobstore.Error
InternalError = blobstore.InternalError
BlobFetchSizeTooLargeError = blobstore.BlobFetchSizeTooLargeError
BlobNotFoundError = blobstore.BlobNotFoundError
DataIndexOutOfRangeError = blobstore.DataIndexOutOfRangeError
PermissionDeniedError = blobstore.PermissionDeniedError
BlobKey: Any
create_rpc = blobstore.create_rpc
create_upload_url = blobstore.create_upload_url
create_upload_url_async = blobstore.create_upload_url_async
delete = blobstore.delete
delete_async = blobstore.delete_async
create_gs_key = blobstore.create_gs_key
create_gs_key_async = blobstore.create_gs_key_async
BLOB_INFO_KIND: Any
BLOB_MIGRATION_KIND: Any
BLOB_KEY_HEADER: Any
BLOB_RANGE_HEADER: Any
MAX_BLOB_FETCH_SIZE: Any
UPLOAD_INFO_CREATION_HEADER: Any
CLOUD_STORAGE_OBJECT_HEADER: Any
GS_PREFIX: Any

class BlobInfoParseError(Error): ...
class FileInfoParseError(Error): ...
class RangeFormatError(Error): ...
class UnsupportedRangeFormatError(RangeFormatError): ...

class _GqlQuery(db.GqlQuery):
    def __init__(self, query_string, model_class, *args, **kwds) -> None: ...

class BlobInfo:
    @property
    def content_type(self): ...
    @property
    def creation(self): ...
    @property
    def filename(self): ...
    @property
    def size(self): ...
    @property
    def md5_hash(self): ...
    @property
    def gs_object_name(self): ...
    def __init__(self, entity_or_blob_key, _values: Any | None = ...) -> None: ...
    @classmethod
    def from_entity(cls, entity): ...
    @classmethod
    def properties(cls): ...
    def key(self): ...
    def delete(self, _token: Any | None = ...) -> None: ...
    def open(self, *args, **kwargs): ...
    @classmethod
    def get(cls, blob_keys): ...
    @classmethod
    def all(cls): ...
    @classmethod
    def gql(cls, query_string, *args, **kwds): ...
    @classmethod
    def kind(self): ...

def get(blob_key): ...
def parse_blob_info(field_storage): ...

class FileInfo:
    def __init__(self, filename: Any | None = ..., content_type: Any | None = ..., creation: Any | None = ..., size: Any | None = ..., md5_hash: Any | None = ..., gs_object_name: Any | None = ...) -> None: ...
    @property
    def filename(self): ...
    @property
    def content_type(self): ...
    @property
    def creation(self): ...
    @property
    def size(self): ...
    @property
    def md5_hash(self): ...
    @property
    def gs_object_name(self): ...

def parse_file_info(field_storage): ...

class BlobReferenceProperty(db.Property):
    data_type: Any
    def get_value_for_datastore(self, model_instance): ...
    def make_value_from_datastore(self, value): ...
    def validate(self, value): ...

def fetch_data(blob, start_index, end_index, rpc: Any | None = ...): ...
def fetch_data_async(blob, start_index, end_index, rpc: Any | None = ...): ...

class BlobReader:
    SEEK_SET: int
    SEEK_CUR: int
    SEEK_END: int
    def __init__(self, blob, buffer_size: int = ..., position: int = ...) -> None: ...
    def __iter__(self): ...
    def close(self) -> None: ...
    def flush(self) -> None: ...
    def next(self): ...
    def __next__(self): ...
    def read(self, size: int = ...): ...
    def readline(self, size: int = ...): ...
    def readlines(self, sizehint: Any | None = ...): ...
    def seek(self, offset, whence=...) -> None: ...
    def tell(self): ...
    def truncate(self, size) -> None: ...
    def write(self, str) -> None: ...
    def writelines(self, sequence) -> None: ...
    @property
    def blob_info(self): ...
    @property
    def closed(self): ...
    def __enter__(self): ...
    def __exit__(self, exc_type, exc_value, traceback) -> None: ...

class BlobMigrationRecord(db.Model):
    new_blob_ref: Any
    @classmethod
    def kind(cls): ...
    @classmethod
    def get_by_blob_key(cls, old_blob_key): ...
    @classmethod
    def get_new_blob_key(cls, old_blob_key): ...

class BlobstoreDownloadHandler:
    def send_blob(self, environ, blob_key_or_info, content_type: Any | None = ..., save_as: Any | None = ..., start: Any | None = ..., end: Any | None = ..., **kwargs): ...
    def get_range(self, environ): ...
    def get(self, environ) -> None: ...
    def __call__(self, environ, start_response): ...

class BlobstoreUploadHandler:
    def __init__(self) -> None: ...
    def get_uploads(self, environ, field_name: Any | None = ...): ...
    def get_file_infos(self, environ, field_name: Any | None = ...): ...
    def post(self, environ) -> None: ...
    def __call__(self, environ, start_response): ...
