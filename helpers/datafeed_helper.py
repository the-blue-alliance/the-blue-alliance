class DatafeedHelper(object):

    @classmethod
    def getTeamKeyNames(self, team_dict):
        """
        Takes a dictionary of teams from USFIRST, and returns a list of team key names.
        """
        team_list = list()
        for team in team_dict:
            team_list.append("frc" + team["number"])

        return team_list

