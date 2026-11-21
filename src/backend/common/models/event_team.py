from typing import cast, Optional, Set

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.models.cached_model import CachedModel
from backend.common.models.event import Event
from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.models.event_team_status import (
    EventTeamStatus,
    EventTeamStatusStrings,
)
from backend.common.models.keys import EventTeamKey, TeamKey, Year
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

    status: EventTeamStatus = cast(EventTeamStatus, ndb.JsonProperty())
    pit_location: EventTeamPitLocation = cast(EventTeamPitLocation, ndb.JsonProperty())
    # Set only on an offseason demo team (e.g. frc9997) that Event.remap_teams maps to a real team's robot.
    # The key the robot competed as in matches, rankings, and awards, e.g. "frc3467B"
    remapped_to: Optional[TeamKey] = ndb.StringProperty(indexed=False)
    # The real team that owns the robot, e.g. "frc3467". Indexed to find all of a team's remapped robots
    remapped_team: Optional[TeamKey] = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _mutable_attrs: Set[str] = {
        "status",
        "year",  # technically immutable, but corruptable and needs repair. See github issue #409
        "pit_location",
        "remapped_to",
        "remapped_team",
    }

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "event": set(),
            "team": set(),
            "year": set(),
            "remapped_team": set(),
        }
        super(EventTeam, self).__init__(*args, **kw)

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
    def competing_team_key(self) -> TeamKey:
        return self.remapped_to or none_throws(self.team.string_id())

    @property
    def status_strings(self) -> EventTeamStatusStrings:
        team_key = self.competing_team_key
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
