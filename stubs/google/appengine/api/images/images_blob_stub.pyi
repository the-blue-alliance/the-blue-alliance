from google.appengine.api import datastore as datastore

BLOB_SERVING_URL_KIND: str

class ImagesBlobStub:
    def __init__(self, host_prefix) -> None: ...
    def GetUrlBase(self, request, response) -> None: ...
    def DeleteUrlBase(self, request, unused_response) -> None: ...
