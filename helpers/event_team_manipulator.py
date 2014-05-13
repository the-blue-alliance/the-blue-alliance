from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase


class EventTeamManipulator(ManipulatorBase):
    """
    Handle EventTeam database writes.
    """
    @classmethod
    def clearCache(self, event_team):
        CacheClearer.clear_eventteam_and_references([event_team.event], [event_team.team], [event_team.year])

    @classmethod
    def updateMerge(self, new_event_team, old_event_team, auto_union=True):
        """
        Update and return EventTeams.
        """
        # build set of referenced keys for cache clearing
        event_keys = set()
        team_keys = set()
        years = set()
        for et in [old_event_team, new_event_team]:
            event_keys.add(et.event)
            team_keys.add(et.team)
            years.add(et.year)

        immutable_attrs = [
            "event",
            "team",
        ]  # These build key_name, and cannot be changed without deleting the model.

        attrs = [
            "year",  # technically immutable, but corruptable and needs repair. See github issue #409
        ]

        for attr in attrs:
            if getattr(new_event_team, attr) is not None:
                if getattr(new_event_team, attr) != getattr(old_event_team, attr):
                    setattr(old_event_team, attr, getattr(new_event_team, attr))
                    old_event_team.dirty = True

        if getattr(old_event_team, 'dirty', False):
            CacheClearer.clear_eventteam_and_references(event_keys, team_keys, years)

        return old_event_team
