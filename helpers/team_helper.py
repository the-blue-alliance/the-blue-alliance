import re
import logging

from google.appengine.api import urlfetch
from google.appengine.ext import db

from models import Team

class TeamTpidHelper(object):
    
    # Separates tpids on the FIRST list of all teams.
    teamRe = re.compile(r'tpid=[A-Za-z0-9=&;\-:]*?"><b>\d+')
    # Extracts the team number from the team result.
    teamNumberRe = re.compile(r'\d+$')
    # Extracts the tpid from the team result.
    tpidRe = re.compile(r'\d+')
    # Extracts the link to the next page of results on the FIRST list of all teams.
    lastPageRe = re.compile(r'Next ->')
    
    @classmethod
    def scrapeTpid(self, number, skip=0):
      """
      Searches the FIRST list of all teams for the requested team's tpid, caching
      all it encounters in the datastore. This has the side effect of creating Team
      objects along the way.
      
      This code is taken directly from Pat Fairbank's frclinks source and modified
      slightly to fit in the TBA framework. He has given us permission to borrow
      his code directly.
      """
      teams_to_put = list()
      while 1:
        
        teamList = urlfetch.fetch(
            'https://my.usfirst.org/myarea/index.lasso?page=searchresults&' +
            'programs=FRC&reports=teams&sort_teams=number&results_size=250&' +
            'omit_searchform=1&season_FRC=2010&skip_teams=' + str(skip),
            deadline=10)
        teamResults = self.teamRe.findall(teamList.content)
        tpid = None
        
        for teamResult in teamResults:
          teamNumber = self.teamNumberRe.findall(teamResult)[0]
          teamTpid = self.tpidRe.findall(teamResult)[0]
          if teamNumber == number:
            tpid = teamTpid
        
          team = Team.get_by_key_name('frc' + str(teamNumber))
          if team is None:
            new_team = Team(
              team_number = int(teamNumber),
              first_tpid = int(teamTpid),
              key_name = "frc" + str(teamNumber)
            )
            teams_to_put.append(new_team)
          else:
            team.first_tpid = int(teamTpid)
            teams_to_put.append(team)
        
        skip = int(skip) + 250
        db.put(teams_to_put)
        teams_to_put = list()
        if tpid:
          return tpid
        if len(self.lastPageRe.findall(teamList.content)) == 0:
          return None


class TeamUpdater(object):
    """
    Helper class to handle Team objects when we are not sure whether they
    already exist or not.
    """

    @classmethod
    def createOrUpdate(self, new_team):
        """
        Check if a team currently exists in the database based on team_number
        If it does, update the team.
        If it does not, create the team.
        """
        query = Team.all()

        # First, do the easy thing and look for an eid collision. 
        # This will only work on USFIRST teams.
        query.filter('team_number =', new_team.team_number)

        if query.count() > 0:
            old_team = query.get()
            new_team = self.updateMerge(new_team, old_team)

        new_team.put()
        return new_team

    @classmethod
    def updateMerge(self, new_team, old_team):
        """
        Given an "old" and a "new" Team object, replace the fields in the
        "old" team that are present in the "new" team, but keep fields from
        the "old" team that are null in the "new" team.
        """
        #FIXME: There must be a way to do this elegantly. -greg 5/12/2010

        if new_team.name is not None:
            old_team.name = new_team.name
        if new_team.nickname is not None:
            old_team.nickname = new_team.nickname
        if new_team.website is not None:
            old_team.website = new_team.website
        if new_team.address is not None:
            old_team.address = new_team.address
        if new_team.first_tpid is not None:
            old_team.first_tpid = new_team.first_tpid
        
        return old_team