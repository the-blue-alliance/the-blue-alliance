import datetime

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.auth_type import AuthType
from backend.common.models.account import Account
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.webcast import Webcast


class ApiAuthAccess(ndb.Model):
    """
    Manages secrets for access to the read and write APIs.
    Models are fetched by ID, which will be some randomly generated alphanumeric string

    For the write API:
    - Access may be granted for more than one event.
    """

    # For both read and write:
    description: str = ndb.TextProperty(indexed=False)  # human-readable description
    auth_types_enum: list[AuthType] = ndb.IntegerProperty(  # pyre-ignore[8]
        choices=list(AuthType), repeated=True
    )  # read and write types should never be mixed
    owner: ndb.Key | None = ndb.KeyProperty(kind=Account)
    allow_admin = ndb.BooleanProperty(default=False)  # Allow access to admin APIv3

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True)

    # Write only:
    secret: str | None = ndb.TextProperty(indexed=False)
    event_list: list[ndb.Key] = ndb.KeyProperty(  # pyre-ignore[8]
        kind=Event, repeated=True
    )  # events for which auth is granted
    # On update, we resolve the events in these districts and add them to event_list
    district_list: list[ndb.Key] = ndb.KeyProperty(  # pyre-ignore[8]
        kind=District, repeated=True
    )
    # Only for offseason events: grant access to MATCH_VIDEO for events whose webcast
    # is here (twitch channel / youtube account)
    offseason_webcast_channels: list[str] = ndb.StringProperty(  # pyre-ignore[8]
        repeated=True
    )
    # Allow access for all events marked official
    all_official_events: bool = ndb.BooleanProperty()
    expiration: datetime.datetime | None = ndb.DateTimeProperty()

    def put(self, *args, **kwargs):
        # Validation for making sure that we never mix the READ_API and other write types together
        if AuthType.READ_API in self.auth_types_enum and not self.auth_types_enum == [
            AuthType.READ_API
        ]:
            raise Exception(
                "Cannot combine AuthType.READ_API with other write auth types"
            )
        return super(ApiAuthAccess, self).put(*args, **kwargs)

    @property
    def can_edit_event_info(self) -> bool:
        return AuthType.EVENT_INFO in self.auth_types_enum

    @property
    def can_edit_event_teams(self) -> bool:
        return AuthType.EVENT_TEAMS in self.auth_types_enum

    @property
    def can_edit_event_matches(self) -> bool:
        return AuthType.EVENT_MATCHES in self.auth_types_enum

    @property
    def can_edit_event_rankings(self) -> bool:
        return AuthType.EVENT_RANKINGS in self.auth_types_enum

    @property
    def can_edit_event_alliances(self) -> bool:
        return AuthType.EVENT_ALLIANCES in self.auth_types_enum

    @property
    def can_edit_event_awards(self) -> bool:
        return AuthType.EVENT_AWARDS in self.auth_types_enum

    @property
    def can_edit_match_video(self) -> bool:
        return AuthType.MATCH_VIDEO in self.auth_types_enum

    @property
    def can_edit_zebra_motionworks(self) -> bool:
        return AuthType.ZEBRA_MOTIONWORKS in self.auth_types_enum

    @property
    def is_read_key(self) -> bool:
        return self.auth_types_enum == [AuthType.READ_API]

    @property
    def is_write_key(self) -> bool:
        return not self.is_read_key

    @property
    def event_list_str(self) -> str:
        return ",".join(
            [none_throws(event_key.string_id()) for event_key in self.event_list]
        )

    @property
    def district_list_str(self) -> str:
        return ",".join(
            [
                none_throws(district_key.string_id())
                for district_key in self.district_list
            ]
        )

    @property
    def webcast_list_str(self) -> str:
        return ",".join(self.offseason_webcast_channels)

    @staticmethod
    def webcast_key(w: Webcast) -> str:
        return f"{w["type"]}:{w["channel"]}"
