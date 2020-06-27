from google.cloud import ndb
from pyre_extensions import safe_cast

from backend.common.models.event import Event
from backend.common.models.event_team_status import EventTeamStatus
from backend.common.models.keys import EventTeamKey
from backend.common.models.team import Team


class EventTeam(ndb.Model):
    """
    EventTeam serves as a join model between Events and Teams, indicating that
    a team will or has competed in an Event.
    key_name is like 2010cmp_frc177 or 2007ct_frc195
    """

    event = ndb.KeyProperty(kind=Event)
    team = ndb.KeyProperty(kind=Team)
    year = ndb.IntegerProperty()

    status: EventTeamStatus = safe_cast(EventTeamStatus, ndb.JsonProperty())

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "event": set(),
            "team": set(),
            "year": set(),
        }
        super(EventTeam, self).__init__(*args, **kw)

    @classmethod
    def validate_key_name(self, key: str) -> bool:
        split = key.split("_")
        return (
            len(split) == 2
            and Event.validate_key_name(split[0])
            and Team.validate_key_name(split[1])
        )

    @property
    def key_name(self) -> EventTeamKey:
        return self.event.id() + "_" + self.team.id()
