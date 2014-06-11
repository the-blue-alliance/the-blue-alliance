from google.appengine.ext import ndb

from models.event import Event


class ApiAuthAccess(ndb.Model):
    """
    Manages secrets for access to the write API.
    Access may be granted for more than one event.
    """
    description = ndb.StringProperty(indexed=False)  # human-readable description
    secret = ndb.StringProperty(indexed=False)
    event_list = ndb.KeyProperty(kind=Event, repeated=True)  # events for which auth is granted
