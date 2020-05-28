import urlparse

from google.appengine.ext import ndb

from models.team import Team
from sitevars.website_blacklist import WebsiteBlacklist


class FIRSTElasticSearchTeamDetailsParser(object):
    def __init__(self, year):
        self.year = int(year)

    def parse(self, response):
        teams = []
        for team in response['hits']['hits']:
            first_tpid = int(team['_id'])
            team = team['_source']

            raw_website = team.get('team_web_url', None)
            website = urlparse.urlparse(raw_website, 'http').geturl() if raw_website else None

            if WebsiteBlacklist.is_blacklisted(website):
                website = ''

            teams.append(Team(
                id="frc{}".format(team['team_number_yearly']),
                team_number=team['team_number_yearly'],
                name=team.get('team_name', None),
                nickname=team.get('team_nickname', None),
                # city=None,
                # state_prov=None,  # team_stateprov isn't in the same format as the FRC API (e.g. 'CA' instead of 'California'). Don't save to avoid unnecessary cache clearing.
                # country=None,
                postalcode=team.get('team_postalcode', None),
                website=website,
                rookie_year=team.get('team_rookieyear', None),
                first_tpid=first_tpid,
                first_tpid_year=self.year,
                motto=team.get('team_motto', None),
            ))

        return teams
