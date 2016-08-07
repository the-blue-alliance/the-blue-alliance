from helpers.cache_clearer import CacheClearer
from helpers.manipulator_base import ManipulatorBase


class TeamManipulator(ManipulatorBase):
    """
    Handle Team database writes.
    """
    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        return CacheClearer.get_team_cache_keys_and_controllers(affected_refs)

    @classmethod
    def updateMerge(self, new_team, old_team, auto_union=True):
        """
        Given an "old" and a "new" Team object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        attrs = [
            "address",
            "city",
            "state_prov",
            "country",
            "name",
            "nickname",
            "website",
            "rookie_year",
            "motto",
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

        return old_team
