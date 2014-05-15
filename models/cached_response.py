from google.appengine.ext import ndb


class CachedResponse(ndb.Model):
    """
    A CachedResponse stores the body of an HTTP response
    key_name is like:
    apiv2_event_controller_2014casj:0:7
    team_detail_frc604_2010:2:7
    """
    body = ndb.TextProperty(required=True)  # not indexed by default

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)
