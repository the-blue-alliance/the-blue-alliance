import re
import logging

from google.appengine.api import urlfetch

from database.match_query import TeamEventMatchesQuery
from helpers.match_helper import MatchHelper
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

    @classmethod
    def generateTeamAtEventStatus(cls, team_key, event):
        team_number = team_key[3:]
        matches_future = TeamEventMatchesQuery(team_key, event.key.id()).fetch_async()
        matches = MatchHelper.organizeMatches(matches_future.get_result())

        # Compute alliances
        alliance_number = None
        if event.alliance_selections:
            for i, alliance in enumerate(event.alliance_selections):
                if team_key in alliance['picks']:
                    alliance_number = i + 1
                    break
            else:
                alliance_number = 0  # Team didn't make it to elims

        level_map = {
            'qf': 'quarters',
            'sf': 'semis',
            'f': 'the finals',
        }
        for comp_level in ['f', 'sf', 'qf']:  # playoffs
            level_str = level_map[comp_level]
            if matches[comp_level]:
                wins = 0
                losses = 0
                for match in matches[comp_level]:
                    if match.has_been_played:
                        if team_key in match.alliances[match.winning_alliance]['teams']:
                            wins += 1
                        else:
                            losses += 1
                if wins == 2:
                    if comp_level == 'f':
                        return "Team {} won the event on alliance #{}.".format(team_number, alliance_number)
                    else:
                        return "Team {} won {} on alliance #{}.".format(team_number, level_str, alliance_number)
                elif losses == 2:
                    return "Team {} got knocked out in {} on alliance #{}.".format(team_number, level_str, alliance_number)
                else:
                    return "Team {} is currently {}-{} in {} on alliance #{}.".format(team_number, wins, losses, level_str, alliance_number)

        # Still in quals or team did not make it to elims
        # Compute qual W-L-T
        wins = 0
        losses = 0
        ties = 0
        unplayed_qual = 0
        for match in matches['qm']:
            if match.has_been_played:
                if match.winning_alliance == '':
                    ties += 1
                elif team_key in match.alliances[match.winning_alliance]['teams']:
                    wins += 1
                else:
                    losses += 1
            else:
                unplayed_qual += 1

        if wins == 0 and losses == 0 and ties == 0:
            # No matches played yet
            return "Team {} has not played any matches yet.".format(team_number)

        # Compute rank & num_teams
        rank = None
        ranking_points = None
        if event.rankings:
            num_teams = len(event.rankings) - 1
            for i, row in enumerate(event.rankings):
                if row[1] == team_number:
                    rank = i
                    ranking_points = int(float(row[2]))
                    break

        if unplayed_qual > 0:
            if rank is not None:
                return "Team {} is currently rank {}/{} with a record of {}-{}-{} and {} ranking points.".format(team_number, rank, num_teams, wins, losses, ties, ranking_points)
            else:
                return "Team {} currently has a record of {}-{}-{}.".format(team_number, wins, losses, ties)
        else:
            if alliance_number is None:
                return "Team {} ended qualification matches at rank {}/{} with a record of {}-{}-{}.".format(team_number, rank, num_teams, wins, losses, ties)
            elif alliance_number == 0:
                return "Team {} ended qualification matches at rank {}/{} with a record of {}-{}-{} and was not picked for playoff matches.".format(team_number, rank, num_teams, wins, losses, ties)
            else:
                return "Team {} will be competing in the playoff matches on alliance #{}.".format(team_number, alliance_number)


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
        logging.info("Fetching 250 teams based on %s data, skipping %s" % (year, skip))

        tpids_dict = dict()

        # FIRST is now checking the 'Referer' header for the string 'usfirst.org'.
        # See https://github.com/patfair/frclinks/commit/051bf91d23ca0242dad5b1e471f78468173f597f
        teamList = urlfetch.fetch(self.TPID_URL_PATTERN % (year, skip), headers={'Referrer': 'usfirst.org'}, deadline=10)
        teamResults = self.teamRe.findall(teamList.content)

        for teamResult in teamResults:
          teamNumber = self.teamNumberRe.findall(teamResult)[0]
          teamTpid = self.tpidRe.findall(teamResult)[0]

          logging.info("Team %s TPID was %s in year %s." % (teamNumber, teamTpid, year))
          tpids_dict[teamNumber] = teamTpid

        teams = [Team(
              team_number=int(team_number),
              first_tpid=int(tpids_dict[team_number]),
              first_tpid_year=int(year),
              id="frc" + str(team_number)
            )
        for team_number in tpids_dict]

        TeamManipulator.createOrUpdate(teams)
        skip = int(skip) + 250

        # Handle degenerate cases.
        if skip > 10000:
          return None

        if len(self.lastPageRe.findall(teamList.content)) == 0:
          return None
