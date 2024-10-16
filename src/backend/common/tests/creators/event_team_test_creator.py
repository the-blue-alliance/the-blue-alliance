from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team


class EventTeamTestCreator(object):
    @classmethod
    def createEventTeams(self, event):
        teams = Team.query().order(Team.team_number).fetch(60)

        event_teams = [
            EventTeam(
                id=event.key.id() + "_" + team.key.id(),
                event=event.key,
                team=team.key,
                year=event.year,
            )
            for team in teams
        ]
        return EventTeamManipulator.createOrUpdate(event_teams)
