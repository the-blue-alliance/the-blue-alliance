from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase


class EventTeamManipulator(ManipulatorBase):
    """
    Handle EventTeam database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_eventteam_cache_keys_and_controllers(affected_refs)

    @classmethod
    def updateMerge(self, new_event_team, old_event_team, auto_union=True):
        """
        Update and return EventTeams.
        """
        immutable_attrs = [
            "event",
            "team",
        ]  # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            "year",  # technically immutable, but corruptable and needs repair. See github issue #409
            "status",
        ]

        for attr in attrs:
            if getattr(new_event_team, attr) is not None:
                if getattr(new_event_team, attr) != getattr(old_event_team, attr):
                    setattr(old_event_team, attr, getattr(new_event_team, attr))
                    old_event_team.dirty = True

        return old_event_team
