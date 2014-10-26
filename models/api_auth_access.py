from google.appengine.ext import ndb

from consts.auth_type import AuthType
from models.event import Event


class ApiAuthAccess(ndb.Model):
    """
    Manages secrets for access to the write API.
    Access may be granted for more than one event.

    Models are fetched by ID, which will be some randomly generated alphanumeric string
    """
    description = ndb.StringProperty(indexed=False)  # human-readable description
    secret = ndb.StringProperty(indexed=False)
    event_list = ndb.KeyProperty(kind=Event, repeated=True)  # events for which auth is granted
    auth_types_enum = ndb.IntegerProperty(repeated=True)

    @property
    def can_edit_event_data(self):
        return AuthType.EVENT_DATA in self.auth_types_enum

    @property
    def can_edit_match_video(self):
        return AuthType.MATCH_VIDEO in self.auth_types_enum
