from google.appengine.ext import ndb

from consts.auth_type import AuthType
from models.account import Account
from models.event import Event


class ApiAuthAccess(ndb.Model):
    """
    Manages secrets for access to the read and write APIs.
    Models are fetched by ID, which will be some randomly generated alphanumeric string

    For the write API:
    - Access may be granted for more than one event.
    """
    # For both read and write:
    description = ndb.StringProperty(indexed=False)  # human-readable description
    auth_types_enum = ndb.IntegerProperty(repeated=True)  # read and write types should never be mixed
    owner = ndb.KeyProperty(kind=Account)
    allow_admin = ndb.BooleanProperty(default=False)  # Allow access to admin APIv3

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)

    # Write only:
    secret = ndb.StringProperty(indexed=False)
    event_list = ndb.KeyProperty(kind=Event, repeated=True)  # events for which auth is granted
    expiration = ndb.DateTimeProperty()

    @property
    def can_edit_event_info(self):
        return AuthType.EVENT_INFO in self.auth_types_enum

    @property
    def can_edit_event_teams(self):
        return AuthType.EVENT_TEAMS in self.auth_types_enum

    @property
    def can_edit_event_matches(self):
        return AuthType.EVENT_MATCHES in self.auth_types_enum

    @property
    def can_edit_event_rankings(self):
        return AuthType.EVENT_RANKINGS in self.auth_types_enum

    @property
    def can_edit_event_alliances(self):
        return AuthType.EVENT_ALLIANCES in self.auth_types_enum

    @property
    def can_edit_event_awards(self):
        return AuthType.EVENT_AWARDS in self.auth_types_enum

    @property
    def can_edit_match_video(self):
        return AuthType.MATCH_VIDEO in self.auth_types_enum

    @property
    def can_edit_zebra_motionworks(self):
        return AuthType.ZEBRA_MOTIONWORKS in self.auth_types_enum

    @property
    def is_read_key(self):
        return self.auth_types_enum == [AuthType.READ_API]

    @property
    def is_write_key(self):
        return not self.is_read_key
