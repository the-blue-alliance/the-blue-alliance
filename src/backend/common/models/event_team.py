from typing import Optional, Set

from google.appengine.ext import ndb
from pyre_extensions import none_throws, safe_cast

from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.models.cached_model import CachedModel
from backend.common.models.event import Event
from backend.common.models.event_team_status import (
    EventTeamStatus,
    EventTeamStatusStrings,
)
from backend.common.models.keys import EventKey, EventTeamKey, TeamKey, Year
from backend.common.models.team import Team


class EventTeam(CachedModel):
    """
    EventTeam serves as a join model between Events and Teams, indicating that
    a team will or has competed in an Event.
    key_name is like 2010cmp_frc177 or 2007ct_frc195
    """

    event: ndb.Key = ndb.KeyProperty(kind=Event, required=True)
    team: ndb.Key = ndb.KeyProperty(kind=Team, required=True)
    year: Year = ndb.IntegerProperty(required=True)

    status: EventTeamStatus = safe_cast(EventTeamStatus, ndb.JsonProperty())

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _mutable_attrs: Set[str] = {
        "status",
        "year",  # technically immutable, but corruptable and needs repair. See github issue #409
    }

    def __init__(
        self, event: ndb.Key, team: ndb.Key, status: Optional[EventTeamStatus] = None
    ):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "event": set(),
            "team": set(),
            "year": set(),
        }

        event_key_name = EventKey(event.id())
        team_key_name = TeamKey(team.id())
        if not Event.validate_key_name(event_key_name):
            raise Exception(f"{event_key_name} is not a valid Event key.")
        if not Team.validate_key_name(team_key_name):
            raise Exception(f"{team_key_name} is not a valid Team key.")
        super(EventTeam, self).__init__(
            id=self.render_key_name(event_key_name, team_key_name),
            event=event,
            team=team,
            year=int(event_key_name[:4]),
            status=status,
        )

    @classmethod
    def render_key_name(
        cls, event_key_name: EventKey, team_key_name: TeamKey
    ) -> EventTeamKey:
        return f"{event_key_name}_{team_key_name}"

    @classmethod
    def validate_key_name(cls, key: str) -> bool:
        split = key.split("_")
        return (
            len(split) == 2
            and Event.validate_key_name(split[0])
            and Team.validate_key_name(split[1])
        )

    @property
    def key_name(self) -> EventTeamKey:
        return (
            none_throws(self.event.string_id())
            + "_"
            + none_throws(self.team.string_id())
        )

    @property
    def status_strings(self) -> EventTeamStatusStrings:
        team_key = none_throws(self.team.string_id())
        return EventTeamStatusStrings(
            alliance=EventTeamStatusHelper.generate_team_at_event_alliance_status_string(
                team_key, self.status
            ),
            playoff=EventTeamStatusHelper.generate_team_at_event_playoff_status_string(
                team_key, self.status
            ),
            overall=EventTeamStatusHelper.generate_team_at_event_status_string(
                team_key, self.status
            ),
        )
