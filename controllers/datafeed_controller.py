import logging
import os
import datetime

from django.utils import simplejson

from google.appengine.api import taskqueue
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

from datafeeds.datafeed_usfirst_events import DatafeedUsfirstEvents
from datafeeds.datafeed_usfirst_matches import DatafeedUsfirstMatches
from datafeeds.datafeed_usfirst_teams import DatafeedUsfirstTeams
from datafeeds.datafeed_tba_videos import DatafeedTbaVideos

from helpers.event_helper import EventUpdater
from helpers.match_helper import MatchUpdater
from helpers.team_helper import TeamTpidHelper, TeamUpdater
from helpers.tbavideo_helper import TBAVideoUpdater
from helpers.opr_helper import OprHelper

from models import Event
from models import EventTeam
from models import Team
from models import Match


class TbaVideosGet(webapp.RequestHandler):
    """
    Handles reading a TBA video listing page and updating the datastore as needed.
    TODO: We never deal with TBAVideos going away.
    """
    def get(self, event_key):
        df = DatafeedTbaVideos()
        
        event = Event.get_by_key_name(event_key)
        tbavideos = df.getEventVideosList(event)
        
        new_tbavideos = list()
        
        if len(tbavideos) < 1:
            logging.info("No tbavideos found for event " + event.key().name())
        else:
            for tbavideo in tbavideos:
                new_tbavideo = TBAVideoUpdater.findOrSpawn(tbavideo) # findOrSpawn doesn't put() things.
                new_tbavideos.append(new_tbavideo)
            
            keys = db.put(new_tbavideos) # Doing a bulk put() is faster than individually.
        
        template_values = {
            'tbavideos': new_tbavideos,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/tba_videos_get.html')
        self.response.out.write(template.render(path, template_values))

class TbaVideosGetEnqueue(webapp.RequestHandler):
    """
    Handles enqueing grabing TBAVideos for individual Events.
    """
    def get(self):
        events = Event.all()

        for event in events.fetch(5000):
            taskqueue.add(
                url='/tasks/tba_videos_get/' + event.key().name(), 
                method='GET')
        
        template_values = {
            'event_count': Event.all().count(),
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/tba_videos_update_enqueue.html')
        self.response.out.write(template.render(path, template_values))

class UsfirstEventsInstantiate(webapp.RequestHandler):
    """
    Handles reading the USFIRST event list.
    Enqueues a bunch of detailed reads that actually establish Event objects.
    """
    def get(self):
        df = DatafeedUsfirstEvents()
        
        try:
            year = self.request.get("year")
            if year == '':
                year = 2012
        except Exception, detail:
            logging.error('Failed to get year value')
        
        # These are dicts with a first_eid
        events = df.getEventList(year)
        
        #TODO: This is only doing Regional events, not Nats -gregmarra 4 Dec 2010
        
        for event in events:
            logging.info("Event with eid: " + str(event.get("first_eid", 0)))
            taskqueue.add(
                url='/tasks/usfirst_event_get/' + event.get("first_eid", 0),
                method='GET')
        
        template_values = {
            'events': events,
            'year': 2010
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_events_instantiate.html')
        self.response.out.write(template.render(path, template_values))

class UsfirstEventGetEnqueue(webapp.RequestHandler):
    """
    Handles enqueing updates to individual USFIRST events.
    """
    def get(self):
        year = 2012 #Just this year #FIXME: Do this right
        events = Event.all()
        events.filter('first_eid != ', None) # Official events with EIDs
        events.filter('year =', year) 
        
        count = 0
        for event in events.fetch(100):
            taskqueue.add(
                url='/tasks/usfirst_event_get/' + event.first_eid, 
                method='GET')
            count += 1
        
        template_values = {
            'event_count': count,
            'year': year,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_events_get_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstEventGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST event page and creating or updating the model as needed.
    Includes registered Teams.
    """
    def get(self, first_eid, year=2012):
        datafeed = DatafeedUsfirstEvents()
        
        event = datafeed.getEvent(first_eid, year)
        event = EventUpdater.createOrUpdate(event)
        
        team_dicts = datafeed.getEventRegistration(first_eid, year)
        teams = Team.get_by_key_name(["frc" + team_dict["number"] for team_dict in team_dicts])
        
        for team_dict, team in zip(team_dicts, teams):
            if team is None:
                team = Team(
                    team_number = int(team_dict["number"]),
                    first_tpid = int(team_dict["tpid"]),
                    key_name = "frc" + str(team_dict["number"])
                )
                team.put()
            
            et = EventTeam.get_or_insert(
                key_name = event.key().name() + "_" + team.key().name(),
                event = event,
                team = team
            )
        
        template_values = {
            'event': event,
            'eventteams_count': len(team_dicts),
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_get.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstMatchesGetEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting match results for USFIRST events.
    """
    def get(self):
        events = Event.all()
        events = events.filter('official =', True)
        
        if self.request.get('now', None) is not None:
            events = events.filter('end_date <=', datetime.date.today() + datetime.timedelta(days=4))
            events = events.filter('end_date >=', datetime.date.today() - datetime.timedelta(days=1))
        else:
            events = events.filter('year =', int(self.request.get('year')))
        
        events = events.fetch(500)
        for event in events:
            taskqueue.add(
                url='/tasks/usfirst_matches_get/' + event.key().name(),
                method='GET')
        
        template_values = {
            'events': events,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_matches_get_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstMatchesGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST match results page and updating the datastore as needed.
    """
    def get(self, event_key):
        df = DatafeedUsfirstMatches()
        mu = MatchUpdater()
        
        event = Event.get_by_key_name(event_key)
        matches = df.getMatchResultsList(event)
        
        new_matches = list()
        if matches is not None:
            mu.bulkRead(matches)
            for match in matches:
                new_match = mu.findOrSpawnWithCache(match) # findOrSpawn doesn't put() things.
                new_matches.append(new_match)
            
            keys = db.put(new_matches) # Doing a bulk put() is faster than individually.
        else:
            logging.info("No matches found for event " + str(event.year) + " " + str(event.name))
        
        template_values = {
            'matches': new_matches,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_matches_get.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstTeamsInstantiate(webapp.RequestHandler):
    """
    A run-as-needed function that instantiates new Team objects based on 
    FIRST's full team list.
    """
    def get(self):
        df = DatafeedUsfirstTeams()
        skip = 0
        year = 2012
        
        try:
            skip = self.request.get("skip")
            if skip == '':
                skip = 0
        except Exception, detail:
            logging.error('Failed to get skip value')
        
        try:
            year = self.request.get("year")
            if year == '':
                year = 2011
        except Exception, detail:
            logging.error('Failed to get year value')
        
        logging.info("YEAR: %s", year)
        df.instantiateTeams(skip, year)
        
        team_count = Team.all().count()
        
        template_values = {
            'team_count': team_count
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_teams_instantiate.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstTeamGetEnqueue(webapp.RequestHandler):
    """
    Handles enqueing updates to individual USFIRST teams.
    """
    def get(self):
        
        offset = int(self.request.get("offset", 0))
        
        teams = Team.all(keys_only=True).fetch(1000, int(offset))
        for team_key in teams:
            taskqueue.add(url='/tasks/usfirst_team_get/' + team_key.name(),
                          method='POST')
                          
        self.response.out.write("%s team gets have been enqueued offset from %s.<br />" %(len(teams), offset))
        self.response.out.write("Reload with ?offset=%s to enqueue more." % (offset + len(teams)))


class UsfirstTeamGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST team information page and updating the
    model accordingly.
    """
    def get(self, key_name):
        df = DatafeedUsfirstTeams()
        
        logging.info("Updating team %s" % key_name)
        team = df.getTeamDetails(key_name[3:])
        logging.info(team)
        if team:
            team = TeamUpdater.createOrUpdate(team)
            success = True
        else:
            success = False
        
        template_values = {
            'team': team,
            'success': success,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_team_get.html')
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


class FlushEventTeams(webapp.RequestHandler):
    """
    NEVER CALL THIS FUNCTION.
    """
    def get(self):
        #500 is max delete at once limit.
        db.delete(EventTeam.all().fetch(500))
        db.delete(EventTeam.all().fetch(500))
        
        eventteam_count = EventTeam.all().count()
        
        self.response.out.write("EventTeams flushed. " + str(eventteam_count) + " EventTeams remain. What have we done?!")


class FlushEvents(webapp.RequestHandler):
    """
    NEVER CALL THIS FUNCTION.
    """
    def get(self):
        db.delete(Event.all().fetch(500))
        
        event_count = Event.all().count()
        
        self.response.out.write("Events flushed. " + str(event_count) + " teams remain. What have we done?!")

class OprGetEnqueue(webapp.RequestHandler):
    """
    Enqueues OPR calculation
    """
    def get(self):
        events = Event.all()
        count = 0
        for event in events:
            taskqueue.add(
                url='/tasks/event_opr_get/' + event.get_key_name(),
                method='GET')
            count = count + 1
            
        template_values = {
            'event_count': count,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/opr_get_enqueue.html')
        self.response.out.write(template.render(path, template_values))

class OprGet(webapp.RequestHandler):
    """
    Calculates the opr for a regional
    """
    def get(self,event_key):
        opr = []
        teams = []
        oprs = []
        event = Event.get_by_key_name(event_key)
        if event.match_set.count()>0:
            opr,teams = OprHelper.opr(event_key)
            oprs.append((opr,teams))
            event.oprs = opr
            event.opr_teams = teams
            event.put()

        template_values = {
            'oprs': oprs,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/opr_get.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        self.get()

        
