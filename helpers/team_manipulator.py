from helpers.manipulator_base import ManipulatorBase

class TeamManipulator(ManipulatorBase):
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
                setattr(old_team, attr, getattr(new_team, attr))
                
        # Take the new tpid and tpid_year iff the year is newer than the old one
        if (new_team.first_tpid_year > old_team.first_tpid_year):
            old_team.first_tpid_year = new_team.first_tpid_year
            old_team.first_tpid = new_team.first_tpid
        
        return old_team
