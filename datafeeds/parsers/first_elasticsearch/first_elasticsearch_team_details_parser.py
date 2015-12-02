from google.appengine.ext import ndb

from models.team import Team


class FIRSTElasticSearchTeamDetailsParser(object):
    def __init__(self, year):
        self.year = int(year)

    def parse(self, response):
        teams = []
        for team in response['hits']['hits']:
            first_tpid = int(team['_id'])
            team = team['_source']

            if 'team_city' in team and 'team_stateprov' in team and 'team_country' in team:
                address = u"{}, {}, {}".format(team['team_city'], team['team_stateprov'], team['team_country'])
            else:
                address = None

            teams.append(Team(
                id="frc{}".format(team['team_number_yearly']),
                team_number=team['team_number_yearly'],
                name=team.get('team_name', None),
                nickname=team['team_nickname'],
                address=address,
                website=team.get('team_web_url', None),
                rookie_year=team.get('team_rookieyear', None),
                first_tpid=first_tpid,
                first_tpid_year=self.year,
                motto=team.get('team_motto', None),
            ))

        return teams
