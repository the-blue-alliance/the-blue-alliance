import logging
import os

from django.utils import simplejson

from google.appengine.api.labs import taskqueue
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

from datafeeds.datafeed_usfirst_events import DatafeedUsfirstEvents
from datafeeds.datafeed_usfirst_matches import DatafeedUsfirstMatches
from datafeeds.datafeed_usfirst_teams import DatafeedUsfirstTeams

from helpers.event_helper import EventUpdater
from helpers.match_helper import MatchUpdater
from helpers.team_helper import TeamTpidHelper, TeamUpdater

from models import Event
from models import Team
from models import Match, MatchScore, MatchTeam

class EnqueueGetUsfirstEvents(webapp.RequestHandler):
    """
    Handles enqueing updates to individual USFIRST events.
    """
    def get(self):
        events = Event.all()
        events.filter('first_eid != ', None) # Official events with EIDs
        
        for event in events.fetch(100):
            taskqueue.add(
                url='/tasks/update_usfirst_event', 
                params={'first_eid':event.first_eid},
                method='GET')

class EnqueueGetUsfirstMatchResults(webapp.RequestHandler):
    """
    Handles enqueing getting match results for USFIRST events.
    """
    def get(self):
        events = Event.all()
        events.filter('official =', True)
        events.filter('year =', int(self.request.get('year')))
        
        try:
            if self.request.get('year') is not None:
                events.filter('year =', int(self.request.get('year')))
        except Exception, detail:
            logging.error('Getting Year Failed: ' + str(detail))
        
        for event in events.fetch(100):
            logging.info(event)
            taskqueue.add(
                url='/tasks/get_usfirst_match_results/' + event.key().name(),
                method='GET')

class EnqueueGetUsfirstTeams(webapp.RequestHandler):
    """
    Handles enqueing updates to individual USFIRST teams.
    """
    def get(self):
        
        offset = self.request.get("offset")
        if (offset is None):
            offset = 0
        
        counter = 0
        for team_key in Team.all(keys_only=True).fetch(1000, int(offset)):
            counter =+ 1
            taskqueue.add(url='/tasks/get_usfirst_team/' + team_key.name(),
                          method='POST')
            
        self.response.out.write(str(counter) + " team gets have been enqueued.<br />")
        self.response.out.write("Reload with ?offset=n to enqueue more.")

class InstantiateRegionalEvents(webapp.RequestHandler):
    """
    Handles reading the USFIRST Regional event list.
    Enqueues a bunch of detailed reads that actually establish
    Event objects.
    """
    def get(self):
        df = DatafeedUsfirstEvents()
        
        # These are dicts with a first_eid
        events = df.getEventList()
        
        for event in events:
            logging.info("Event with eid: " + str(event.get("first_eid", None)))
            taskqueue.add(
                url='/tasks/update_usfirst_event',
                params={'first_eid':event.get("first_eid", None)},
                method='GET')
        
        template_values = {
            'events': events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/test_datafeed_usfirst_regional_events.html')
        self.response.out.write(template.render(path, template_values))

class GetUsfirstEvent(webapp.RequestHandler):
    """
    Handles reading a USFIRST event page and creating or updating the model as needed.
    """
    def get(self):
        df = DatafeedUsfirstEvents()
        
        first_eid = self.request.get('first_eid')
        event = df.getEvent(first_eid)
        
        event = EventUpdater.createOrUpdate(event)

        template_values = {
            'events': [event],
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/test_datafeed_usfirst_regional_events.html')
        self.response.out.write(template.render(path, template_values))

class GetUsfirstMatchResults(webapp.RequestHandler):
    """
    Handles reading a USFIRST match results page and updating the datastore as needed.
    Pushes Match Result Scores and Alliances to a deferred Handler because we're inefficient
    about them right now.
    """
    def get(self, event_key):
        df = DatafeedUsfirstMatches()
        
        event = Event.get_by_key_name(event_key)
        matches = df.getMatchResultsList(event)
        
        new_matches = list()
        
        if matches is None:
            logging.info("No matches found for event " + str(event.year) + " " + str(event.name))
        else:
            for match in matches:
                new_match = MatchUpdater.findOrSpawn(match) # findOrSpawn doesn't put() things.
                new_matches.append(new_match)
            
            keys = db.put(new_matches) # Doing a bulk put() is faster than individually.
        
        template_values = {
            'matches': new_matches,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/test_datafeed_usfirst_match_results.html')
        self.response.out.write(template.render(path, template_values))


class InstantiateUsfirstTeams(webapp.RequestHandler):
    """
    A run-as-needed function that instantiates new Team objects based on 
    FIRST's full team list.
    """
    def get(self):
        df = DatafeedUsfirstTeams()
        skip = 0
        try:
            skip = self.request.get("skip")
            if skip == '':
                skip = 0
        except Exception, detail:
            logging.error('Failed to get skip value')
        
        df.instantiateTeams(skip)
        
        team_count = Team.all().count()
        
        template_values = {
            'team_count': team_count
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/test_datafeed_instantiate_usfirst_teams.html')
        self.response.out.write(template.render(path, template_values))

class GetUsfirstTeam(webapp.RequestHandler):
    """
    Handles reading a USFIRST team information page and updating the
    model accordingly.
    """
    def get(self, key_name):
        df = DatafeedUsfirstTeams()

        old_team = Team.get_by_key_name(key_name)

        logging.info("Updating team " + str(old_team.team_number))
        new_team = df.getTeamDetails(old_team.team_number)
        team = TeamUpdater.createOrUpdate(new_team)

        template_values = {
            'team': team,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/team.html')
        self.response.out.write(template.render(path, template_values))

    def post(self, key_name):
        self.get(key_name)

class FlushTeams(webapp.RequestHandler):
    """
    NEVER CALL THIS FUNCTION.
    """
    def get(self):
        df = DatafeedUsfirstTeams()
        df.flushTeams()
        
        team_count = Team.all().count()
        
        self.response.out.write("Teams flushed. " + str(team_count) + " teams remain. What have we done?!")

class FlushMatches(webapp.RequestHandler):
    """
    NEVER CALL THIS FUNCTION.
    """
    def get(self):
        #500 is max delete at once limit.
        db.delete(Match.all().fetch(500))
        
        match_count = Match.all().count()
        
        template_values = {
            'match_count': match_count,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/matches/flush.html')
        self.response.out.write(template.render(path, template_values))
        
class FlushEvents(webapp.RequestHandler):
    """
    NEVER CALL THIS FUNCTION.
    """
    def get(self):
        db.delete(Event.all().fetch(500))

        event_count = Event.all().count()
        
        self.response.out.write("Events flushed. " + str(event_count) + " teams remain. What have we done?!")

        