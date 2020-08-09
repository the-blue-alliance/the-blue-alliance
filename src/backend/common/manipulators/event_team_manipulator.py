from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.event_team import EventTeam


class EventTeamManipulator(ManipulatorBase[EventTeam]):
    """
    Handle EventTeam database writes.
    """

    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_eventteam_cache_keys_and_controllers(affected_refs)
    """

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
        cls._update_attrs(new_event_team, old_event_team)
        return old_event_team
