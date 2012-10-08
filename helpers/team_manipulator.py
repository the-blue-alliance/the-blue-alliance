from helpers.ndb_manipulator_base import NdbManipulatorBase

class TeamManipulator(NdbManipulatorBase):
    """
    Handle Team database writes.
    """
    
    @classmethod
    def updateMerge(self, new_team, old_team):
        """
        Given an "old" and a "new" Team object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        attrs = [
            "address",
            "name",
            "nickname",
            "website",
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
