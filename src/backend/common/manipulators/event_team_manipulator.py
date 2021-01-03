from typing import List

from backend.common.cache_clearing import get_affected_queries
from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import TAffectedReferences
from backend.common.models.event_team import EventTeam


class EventTeamManipulator(ManipulatorBase[EventTeam]):
    """
    Handle EventTeam database writes.
    """

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[get_affected_queries.TCacheKeyAndQuery]:
        return get_affected_queries.eventteam_updated(affected_refs)

    @classmethod
    def updateMerge(
        cls,
        new_event_team: EventTeam,
        old_event_team: EventTeam,
        auto_union: bool = True,
    ) -> EventTeam:
        """
        Update and return EventTeams.
        """
        cls._update_attrs(new_event_team, old_event_team, auto_union)
        return old_event_team
