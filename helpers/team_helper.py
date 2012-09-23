import re
import logging

from google.appengine.api import urlfetch
from google.appengine.ext import db

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
    def scrapeTpid(self, number, skip=0, year=2012):
      """
      Searches the FIRST list of all teams for the requested team's tpid, caching
      all it encounters in the datastore. This has the side effect of creating Team
      objects along the way.
      
      This code is modified from Pat Fairbank's frclinks source and modified
      to fit in the TBA framework. He has given us permission to borrow
      his code.
      """
      while 1:
        logging.info("Fetching 250 teams based on %s data, skipping %s" % (year, skip))
        
        tpid = None
        tpids_dict = dict()
        
        teamList = urlfetch.fetch(self.TPID_URL_PATTERN % (year, skip), deadline=10)
        teamResults = self.teamRe.findall(teamList.content)
        
        for teamResult in teamResults:
          teamNumber = self.teamNumberRe.findall(teamResult)[0]
          teamTpid = self.tpidRe.findall(teamResult)[0]
          
          logging.info("Team %s TPID was %s in year %s." % (teamNumber, teamTpid, year))
          tpids_dict[int(teamNumber)] = teamTpid
          
          # If this was the team we were looking for, write it down so we can return it
          if teamNumber == number:
            tpid = teamTpid
        
        # Bulk fetching teams is much more efficient.
        teams = Team.get([db.Key.from_path("Team", "frc" + str(a)) for a in tpids_dict.keys()])
        team_dict = dict([[int(team.team_number), team] for team in teams if team])
        
        teams_to_put = list()
        for team_number in tpids_dict:
          new_team = Team(
              team_number = int(team_number),
              first_tpid = int(tpids_dict[team_number]),
              first_tpid_year = int(year),
              key_name = "frc" + str(team_number)
            )
          
          if team_number not in team_dict:
            teams_to_put.append(new_team)
          else:
            teams_to_put.append(TeamUpdater.updateMerge(new_team, team_dict[team_number]))
        
        db.put(teams_to_put)
        skip = int(skip) + 250
        
        # Return if we found the TPID we wanted, or we're out of teams
        if tpid:
          return tpid
        
        if len(self.lastPageRe.findall(teamList.content)) == 0:
          return None


class TeamUpdater(object):
    """
    DEPRECATED for TeamManipulator. -gregmarra 20120921

    Helper class to handle Team objects when we are not sure whether they
    already exist or not.
    """
    
    @classmethod
    def bulkCreateOrUpdate(self, new_teams):
        put_teams = []
        while len(new_teams) > 0:
            team_batch = new_teams[-500:] # the last 500 items (or all of them)
            new_teams = new_teams[:-500] # everything but the last 500 items (or nothing)
            
            old_teams = Team.get_by_key_name([team.key().name() for team in team_batch])
            teams_to_put = [self.updateMerge(new_team, old_team) for (new_team, old_team) in zip(team_batch, old_teams)]
            db.put(teams_to_put)
            put_teams.extend(teams_to_put)
        return put_teams

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
        
        if old_team is None:
            return new_team

        if new_team.name:
            old_team.name = new_team.name
        if new_team.nickname:
            old_team.nickname = new_team.nickname
        if new_team.website:
            old_team.website = new_team.website
        if new_team.address:
            old_team.address = new_team.address
        
        # Take the new tpid and tpid_year iff the year is newer than the old one
        if (new_team.first_tpid_year > old_team.first_tpid_year):
            old_team.first_tpid_year = new_team.first_tpid_year
            old_team.first_tpid = new_team.first_tpid
        
        return old_team
