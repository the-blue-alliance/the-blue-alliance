import json
from google.appengine.ext import ndb


class CachedResponse(ndb.Model):
    """
    A CachedResponse stores the body of an HTTP response
    key_name is like:
    apiv2_event_controller_2014casj:0:7
    team_detail_frc604_2010:2:7
    """
    headers_json = ndb.TextProperty(required=True)  # not indexed by default
    body = ndb.TextProperty(required=True)  # not indexed by default

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        self._headers = None
        super(CachedResponse, self).__init__(*args, **kw)

    @property
    def headers(self):
        """
        Lazy load headers_json
        """
        if self._headers is None:
            self._headers = {}
            for key, value in json.loads(self.headers_json).items():
                self._headers[str(key)] = str(value)
        return self._headers
