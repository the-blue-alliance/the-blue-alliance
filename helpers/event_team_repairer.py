from models.event_team import EventTeam


class EventTeamRepairer(object):
    """
    Repair corrupt EventTeam objects.
    """

    @classmethod
    def repair(self, event_teams):
        """
        Repair missing year attributes by rebuilding from Event key value.
        """
        new_event_teams = list()

        for event_team in event_teams:
            if event_team.year == None:
                # Note, y10k bug. -gregmarra
                new_event_teams.append(EventTeam(
                    id='{}_{}'.format(event_team.event.id(), event_team.team.id()),
                    event=event_team.event,
                    team=event_team.team,
                    year=int(event_team.event.id()[:4])))

        return new_event_teams
