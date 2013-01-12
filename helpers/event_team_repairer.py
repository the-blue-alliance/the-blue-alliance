import logging

class EventTeamRepairer(object):
    """
    Repair corrupt EventTeam objects.
    """

    @classmethod
    def repair(self, event_teams):
        """
        Repair missing year attributes by rebuilding from Event key value.
        """
        for event_team in event_teams:
            if event_team.year == None:
                # Note, y10k bug. -gregmarra
                event_team.year = int(event_team.event.id()[:4])

        return event_teams
