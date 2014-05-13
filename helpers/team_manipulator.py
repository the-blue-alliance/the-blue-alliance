from cache_clearer.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase


class TeamManipulator(ManipulatorBase):
    """
    Handle Team database writes.
    """
    @classmethod
    def clearCache(self, team):
        CacheClearer.clear_team_and_references([team.key])

    @classmethod
    def updateMerge(self, new_team, old_team, auto_union=True):
        """
        Given an "old" and a "new" Team object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        # build set of referenced keys for cache clearing
        team_keys = set()
        for t in [old_team, new_team]:
            team_keys.add(t.key)

        attrs = [
            "address",
            "name",
            "nickname",
            "website",
            "rookie_year",
        ]

        for attr in attrs:
            if getattr(new_team, attr) is not None:
                if getattr(new_team, attr) != getattr(old_team, attr):
                    setattr(old_team, attr, getattr(new_team, attr))
                    old_team.dirty = True

        # Take the new tpid and tpid_year iff the year is newer than the old one
        if (new_team.first_tpid_year > old_team.first_tpid_year):
            old_team.first_tpid_year = new_team.first_tpid_year
            old_team.first_tpid = new_team.first_tpid
            old_team.dirty = True

        if getattr(old_team, 'dirty', False):
            CacheClearer.clear_team_and_references(team_keys)

        return old_team
