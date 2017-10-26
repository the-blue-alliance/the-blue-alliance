from helpers.team_manipulator import TeamManipulator
from models.team import Team


class TeamTestCreator(object):

    TEAMS = [
        "Red Jaguars", "Blue Barracudas", "Green Monkeys", "Orange Iguanas",
        "Purple Parrots", "Silver Snakes"
    ]

    @classmethod
    def createTeam(cls, number, name=None):
        team = Team(
            id="frc{}".format(number),
            team_number=number,
            name=name,
            nickname=name,
        )
        team = TeamManipulator.createOrUpdate(team)
        return team

    @classmethod
    def createSixTeams(cls):
        teams = []
        for n in range(1, 7):
            teams.append(cls.createTeam(n, cls.TEAMS[n - 1]))
        return teams
