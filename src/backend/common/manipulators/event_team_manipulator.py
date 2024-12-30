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
        new_model: EventTeam,
        old_model: EventTeam,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> EventTeam:
        """
        Update and return EventTeams.
        """
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model
