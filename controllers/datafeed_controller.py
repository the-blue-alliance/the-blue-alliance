import logging
import os
import datetime
import json

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from datafeeds.datafeed_fms import DatafeedFms
from datafeeds.datafeed_tba import DatafeedTba
from datafeeds.datafeed_usfirst import DatafeedUsfirst

from helpers.event_manipulator import EventManipulator
from helpers.match_manipulator import MatchManipulator
from helpers.award_manipulator import AwardManipulator
from helpers.team_helper import TeamHelper, TeamTpidHelper
from helpers.team_manipulator import TeamManipulator

from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

class FmsEventListGet(webapp.RequestHandler):
    """
    Fetch basic data about all current season events at once.
    """
    def get(self):
        df = DatafeedFms()
        events = df.getFmsEventList()

        # filter if first_eid is too high, meaning its a Championship Division
        # (we manually add these due to naming issues)
        events = filter(lambda e: int(e.first_eid) < 100000, events)
        
        events = EventManipulator.createOrUpdate(events)

        template_values = {
            "events": events
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/fms_event_list_get.html')
        self.response.out.write(template.render(path, template_values))


class FmsTeamListGet(webapp.RequestHandler):
    """
    Fetch basic data about all current season teams at once.
    Doesn't get tpids or full data.
    """
    def get(self):
        df = DatafeedFms()
        teams = df.getFmsTeamList()
        TeamManipulator.createOrUpdate(teams)
        
        template_values = {
            "teams": teams
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/fms_team_list_get.html')
        self.response.out.write(template.render(path, template_values))


class TbaVideosEnqueue(webapp.RequestHandler):
    """
    Handles enqueing grabing tba_videos for Matches at individual Events.
    """
    def get(self):
        events = Event.query()

        for event in events:
            taskqueue.add(
                url='/tasks/get/tba_videos/' + event.key_name, 
                method='GET')
        
        template_values = {
            'event_count': Event.query().count(),
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/tba_videos_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class TbaVideosGet(webapp.RequestHandler):
    """
    Handles reading a TBA video listing page and updating the match objects in the datastore as needed.
    """
    def get(self, event_key):
        df = DatafeedTba()
        
        event = Event.get_by_id(event_key)
        match_filetypes = df.getVideos(event)
        if match_filetypes:
            matches_to_put = []
            for match in Match.query(Match.event == event.key).fetch(500):
                if match.tba_videos != match_filetypes.get(match.key_name, []):
                    match.tba_videos = match_filetypes.get(match.key_name, [])
                    matches_to_put.append(match)
            
            MatchManipulator.createOrUpdate(matches_to_put)
            
            tbavideos = match_filetypes.items()
        else:
            logging.info("No tbavideos found for event " + event.key_name)
            tbavideos = []
        
        template_values = {
            'tbavideos': tbavideos,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/tba_videos_get.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstEventDetailsEnqueue(webapp.RequestHandler):
    """
    Handles enqueing updates to individual USFIRST events.
    """
    def get(self, year):
        events = Event.query(Event.first_eid != None, Event.year == int(year))
        
        for event in events.fetch(200):
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_event_details/%s/%s' % (year, event.first_eid),
                method='GET')
        
        template_values = {
            'event_count': events.count(),
            'year': year,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_events_details_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstEventDetailsGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST event page and creating or updating the model as needed.
    Includes registered Teams.
    """
    def get(self, year, first_eid):
        datafeed = DatafeedUsfirst()

        event = datafeed.getEventDetails(int(year), first_eid)
        event = EventManipulator.createOrUpdate(event)
        
        new_teams = datafeed.getEventTeams(int(year), first_eid)
        old_teams = ndb.get_multi([new_team.key for new_team in new_teams])
        
        for new_team, team in zip(new_teams, old_teams):
            if team is None:
                team = new_team
                team.put()
            
            et = EventTeam.get_or_insert(
                event.key_name + "_" + team.key_name,
                event = event.key,
                team = team.key
            )
        
        template_values = {
            'event': event,
            'eventteams_count': len(new_teams),
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_details_get.html')
        self.response.out.write(template.render(path, template_values))

class UsfirstAwardsEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting awards for USFIRST events.
    """
    def get(self, when):
        events = Event.query()
        events = events.filter(Event.official == True)
        
        if when == "now":
            events = events.filter(Event.end_date <= datetime.datetime.today() + datetime.timedelta(days=4))
            events = events.filter(Event.end_date >= datetime.datetime.today() - datetime.timedelta(days=1))
        else:
            events = events.filter(Event.year == int(when))
        
        events = events.fetch(500)
        
        for event in events:
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_awards/%s' % (event.key_name),
                method='GET')
        template_values = {
            'events': events,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_awards_enqueue.html')
        self.response.out.write(template.render(path, template_values))

class UsfirstAwardsGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST match results page and updating the datastore as needed.
    """
    def get(self, event_key):   
        datafeed = DatafeedUsfirst()
        
        event = Event.get_by_id(event_key)
        new_awards = AwardManipulator.createOrUpdate(datafeed.getEventAwards(event))
        
        template_values = {
            'awards': new_awards,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_awards_get.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstEventListGet(webapp.RequestHandler):
    """
    Handles reading the USFIRST event list.
    Enqueues a bunch of detailed reads that actually establish Event objects.
    """
    def get(self, year):
        df = DatafeedUsfirst()
        events = df.getEventList(int(year))
        
        for event in events:
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_event_details/%s/%s' % (year, event.first_eid),
                method='GET')
        
        template_values = {
            'events': events,
            'year': year
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_list_get.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstMatchesEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting match results for USFIRST events.
    """
    def get(self, when):
        events = Event.query(Event.official == True)
        
        if when == "now":
            events = events.filter(Event.end_date <= datetime.datetime.today() + datetime.timedelta(days=4))
            events = events.filter(Event.end_date >= datetime.date.today() - datetime.timedelta(days=1))
        else:
            events = events.filter(Event.year == int(when))
        
        events = events.fetch(500)
        for event in events:
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_matches/' + event.key_name,
                method='GET')
        
        template_values = {
            'events': events,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_matches_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstMatchesGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST match results page and updating the datastore as needed.
    """
    def get(self, event_key):
        df = DatafeedUsfirst()
        
        event = Event.get_by_id(event_key)
        new_matches = MatchManipulator.createOrUpdate(df.getMatches(event))

        template_values = {
            'matches': new_matches,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_matches_get.html')
        self.response.out.write(template.render(path, template_values))
        
        
class UsfirstEventRankingsEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting rankings for USFIRST events.
    """
    def get(self, when):
        events = Event.query()
        events = events.filter(Event.official == True)
        
        if when == "now":
            events = events.filter(Event.end_date <= datetime.datetime.today() + datetime.timedelta(days=4))
            events = events.filter(Event.end_date >= datetime.datetime.today() - datetime.timedelta(days=1))
        else:
            events = events.filter(Event.year == int(when))
        
        events = events.fetch(500)
        for event in events:
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_event_rankings/' + event.key_name,
                method='GET')
        
        template_values = {
            'events': events,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_rankings_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstEventRankingsGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST ranking page and updating the datastore as needed.
    """
    def get(self, event_key):
        df = DatafeedUsfirst()
        
        event = Event.get_by_id(event_key)
        rankings = df.getEventRankings(event)
        event.rankings_json = json.dumps(rankings)
        event.put()

        # TODO update to use Manipulators -gregmarra 20121006

        template_values = {'rankings': rankings,
                           'event_name': event.key_name}
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_rankings_get.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstTeamDetailsEnqueue(webapp.RequestHandler):
    """
    Handles enqueing updates to individual USFIRST teams.
    """
    def get(self):
        offset = int(self.request.get("offset", 0))
        
        teams = Team.query().fetch(1000, offset=int(offset))
        for team_key in teams:
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_team_details/' + team_key.id(),
                method='GET')
        
        # FIXME omg we're just writing out? -gregmarra 2012 Aug 26
        self.response.out.write("%s team gets have been enqueued offset from %s.<br />" %(len(teams), offset))
        self.response.out.write("Reload with ?offset=%s to enqueue more." % (offset + len(teams)))


class UsfirstTeamDetailsGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST team information page and updating the
    model accordingly.
    """
    def get(self, key_name):
        df = DatafeedUsfirst()
        team = df.getTeamDetails(Team.get_by_id(key_name))
        if team:
            team = TeamManipulator.createOrUpdate(team)
            success = True
        else:
            success = False
        
        template_values = {
            'team': team,
            'success': success,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_team_details_get.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstTeamsTpidsGet(webapp.RequestHandler):
    """
    A run-as-needed function that instantiates new Team objects based on 
    FIRST's full team list.
    """
    def get(self, year):
        df = DatafeedUsfirst()
        skip = 0
        
        try:
            skip = self.request.get("skip")
            if skip == '':
                skip = 0
        except Exception, detail:
            logging.error('Failed to get skip value')
        
        logging.info("YEAR: %s", year)
        df.getTeamsTpids(int(year), skip)
        
        team_count = Team.query().count()
        
        template_values = {
            'team_count': team_count
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_teams_tpids.html')
        self.response.out.write(template.render(path, template_values))
