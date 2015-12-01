from google.appengine.ext import ndb

from models.team import Team


class FIRSTElasticSearchTeamDetailsParser(object):
    def __init__(self, year):
        self.year = year

    def parse(self, response):
        teams = []
        for team in response['hits']['hits']:
            team = team['_source']

            address = u"{}, {}, {}".format(team['team_city'], team['team_stateprov'], team['team_country'])

            teams.append(Team(
                id="frc{}".format(team['team_number_yearly']),
                team_number=team['team_number_yearly'],
                name=None,  # Not consistently returned by API for some reason
                nickname=team['team_nickname'],
                address=address,
                website=team.get('team_web_url', None),
                rookie_year=team['team_rookieyear']
            ))

        return teams
