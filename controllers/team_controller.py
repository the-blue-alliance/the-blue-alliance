import datetime
import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import tba_config
from base_controller import BaseHandler, CacheableHandler
from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper
from helpers.award_helper import AwardHelper
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team
from models.award import Award

# The view of a list of teams.
class TeamList(CacheableHandler):

    VALID_PAGES = [1, 2, 3, 4, 5]

    def __init__(self, *args, **kw):
        super(TeamList, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "team_list_{}" # (page)
        self._cache_version = 1

    def get(self, page='1'):
        if page == '':
            return self.redirect("/teams")
        page = int(page)
        if page not in self.VALID_PAGES:
            return self.redirect("/error/404")

        self._cache_key = self._cache_key.format(page)
        super(TeamList, self).get(page)

    def _render(self, page=''):
        page_labels = []
        for curPage in self.VALID_PAGES:
            if curPage == 1:
                label = '1-999'
            else:
                label = "{}'s".format((curPage - 1)*1000)
            page_labels.append(label)
            if curPage == page:
                cur_page_label = label
                                   
        start = (page - 1) * 1000
        stop = start + 999
        teams = Team.query().order(Team.team_number).filter(Team.team_number >= start).filter(Team.team_number < stop).fetch(10000)        

        num_teams = len(teams)
        middle_value = num_teams/2
        if num_teams%2 != 0:
            middle_value += 1
        teams_a, teams_b = teams[:middle_value], teams[middle_value:]

        template_values = {
            "teams_a": teams_a,
            "teams_b": teams_b,
            "num_teams": num_teams,
            "page_labels": page_labels,
            "cur_page_label": cur_page_label,
            "current_page": page
        }
    
        path = os.path.join(os.path.dirname(__file__), '../templates/team_list.html')
        return template.render(path, template_values)
        
# The view of a single Team.
class TeamDetail(CacheableHandler):

    def __init__(self, *args, **kw):
        super(TeamDetail, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 5
        self._cache_key = "team_detail_{}_{}_{}" # (team_number, year, explicit_year)
        self._cache_version = 2

    def get(self, team_number, year=None, explicit_year=False):
        
        # /team/0201 should redirect to /team/201
        try:
            if str(int(team_number)) != team_number:
                if year is None:
                    return self.redirect("/team/%s" % int(team_number))
                else:
                    return self.redirect("/team/%s/%s" % (int(team_number), year))
        except ValueError, e:
            logging.info("%s", e)
            return self.redirect("/error/404")
        
        if type(year) == str: 
            try:
                year = int(year)
            except ValueError, e:
                logging.info("%s", e)
                return self.redirect("/team/%s" % team_number)
            explicit_year = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False
        
        self._cache_key = self._cache_key.format("frc" + team_number, year, explicit_year)
        super(TeamDetail, self).get(team_number, year, explicit_year)

    def _render(self, team_number, year=None, explicit_year=False):
        team = Team.get_by_id("frc" + team_number)
        
        if not team:
            return self.redirect("/error/404")
        
        event_teams = EventTeam.query(EventTeam.team == team.key).fetch(1000)
        event_keys = [event_team.event for event_team in event_teams if event_team.year == year]
        events = ndb.get_multi(event_keys)

        for event in events:
            if not event.start_date:
                event.start_date = datetime.datetime(year, 12, 31) #unknown goes last
        events = sorted(events, key=lambda event: event.start_date)
        
        years = sorted(set([a.year for a in event_teams if a.year != None]))
        
        # Prepare the data to batch it with ndb
        for e in events:
            e.team_matches_future = Match.query(Match.event == e.key, Match.team_key_names == team.key_name).fetch_async(500)
            e.team_awards_future = Award.query(Award.event == e.key, Award.team == team.key).fetch_async(500)

        # Return an array of event names and a list of matches from that event that the
        # team was a participant in.
        participation = list()
        year_wlt_list = list()

        for e in events:
            awards = AwardHelper.organizeAwards(e.team_awards_future.get_result())
            matches = e.team_matches_future.get_result()
            matches_organized = MatchHelper.organizeMatches(matches)

            wlt = EventHelper.calculateTeamWLTFromMatches(team.key_name, matches)
            year_wlt_list.append(wlt)
            if wlt["win"] + wlt["loss"] + wlt["tie"] == 0:
                display_wlt = None
            else:
                display_wlt = wlt
                
            team_rank = None
            if e.rankings:
                for element in e.rankings:
                    if element[1] == team_number:
                        team_rank = element[0]
                        break
                
                
            participation.append({ 'event' : e,
                                   'matches' : matches_organized,
                                   'wlt': display_wlt,
                                   'rank': team_rank,
                                   'awards': awards })
        
        year_wlt = {"win": 0, "loss": 0, "tie": 0}
        for wlt in year_wlt_list:
            year_wlt["win"] += wlt["win"]
            year_wlt["loss"] += wlt["loss"]
            year_wlt["tie"] += wlt["tie"]
        if year_wlt["win"] + year_wlt["loss"] + year_wlt["tie"] == 0:
            year_wlt = None
        
        template_values = { "explicit_year": explicit_year,
                            "team": team,
                            "participation": participation,
                            "year": year,
                            "years": years,
                            "year_wlt": year_wlt }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/team_details.html')
        return template.render(path, template_values)
