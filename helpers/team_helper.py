import re
import logging

from google.appengine.api import urlfetch

from helpers.team_manipulator import TeamManipulator
from models.team import Team


class TeamHelper(object):
    """
    Helper to sort teams and stuff
    """

    @classmethod
    def sortTeams(self, team_list):
        """
        Takes a list of Teams (not a Query object).
        """
        # Sometimes there are None objects in the list.
        team_list = filter(None, team_list)
        team_list = sorted(team_list, key=lambda team: team.team_number)

        return team_list


class TeamTpidHelper(object):

    # Separates tpids on the FIRST list of all teams.
    teamRe = re.compile(r'tpid=[A-Za-z0-9=&;\-:]*?"><b>\d+')
    # Extracts the team number from the team result.
    teamNumberRe = re.compile(r'\d+$')
    # Extracts the tpid from the team result.
    tpidRe = re.compile(r'\d+')
    # Extracts the link to the next page of results on the FIRST list of all teams.
    lastPageRe = re.compile(r'Next ->')

    TPID_URL_PATTERN = "https://my.usfirst.org/myarea/index.lasso?page=searchresults&programs=FRC&reports=teams&sort_teams=number&results_size=250&omit_searchform=1&season_FRC=%s&skip_teams=%s"

    @classmethod
    def scrapeTpids(self, skip, year):
        """
      Searches the FIRST list of all teams for tpids, writing in the datastore.
      Also creates new Team objects.

      This code is modified from Pat Fairbank's frclinks source and modified
      to fit in the TBA framework. He has given us permission to borrow
      his code.
      """
        while 1:
            logging.info("Fetching 250 teams based on %s data, skipping %s" %
                         (year, skip))

            tpids_dict = dict()

            # FIRST is now checking the 'Referer' header for the string 'usfirst.org'.
            # See https://github.com/patfair/frclinks/commit/051bf91d23ca0242dad5b1e471f78468173f597f
            teamList = urlfetch.fetch(
                self.TPID_URL_PATTERN % (year, skip),
                headers={'Referrer': 'usfirst.org'},
                deadline=10)
            teamResults = self.teamRe.findall(teamList.content)

            for teamResult in teamResults:
                teamNumber = self.teamNumberRe.findall(teamResult)[0]
                teamTpid = self.tpidRe.findall(teamResult)[0]

                logging.info("Team %s TPID was %s in year %s." %
                             (teamNumber, teamTpid, year))
                tpids_dict[teamNumber] = teamTpid

            teams = [
                Team(
                    team_number=int(team_number),
                    first_tpid=int(tpids_dict[team_number]),
                    first_tpid_year=int(year),
                    id="frc" + str(team_number)) for team_number in tpids_dict
            ]

            TeamManipulator.createOrUpdate(teams)
            skip = int(skip) + 250

            # Handle degenerate cases.
            if skip > 10000:
                return None

            if len(self.lastPageRe.findall(teamList.content)) == 0:
                return None
