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
        #FIXME: There must be a way to do this elegantly. -greg 5/12/2010
        
        if new_team.name:
            old_team.name = new_team.name
        if new_team.nickname:
            old_team.nickname = new_team.nickname
        if new_team.website:
            old_team.website = new_team.website
        if new_team.address:
            old_team.address = new_team.address
        
        # Take the new tpid and tpid_year iff the year is newer than the old one
        if (new_team.first_tpid_year > old_team.first_tpid_year):
            old_team.first_tpid_year = new_team.first_tpid_year
            old_team.first_tpid = new_team.first_tpid
        
        return old_team
