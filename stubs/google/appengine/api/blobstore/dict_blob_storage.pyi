from google.appengine.api import blobstore as blobstore
from google.appengine.api.blobstore import blob_storage as blob_storage

class DictBlobStorage(blob_storage.BlobStorage):
    def __init__(self) -> None: ...
    def StoreBlob(self, blob_key, blob_stream) -> None: ...
    def CreateBlob(self, blob_key, blob) -> None: ...
    def OpenBlob(self, blob_key): ...
    def DeleteBlob(self, blob_key) -> None: ...
