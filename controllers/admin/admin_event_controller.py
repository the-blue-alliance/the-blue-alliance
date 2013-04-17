from datetime import datetime
import json
import logging
import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from helpers.event.event_test_creator import EventTestCreator
from helpers.event_manipulator import EventManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.match_manipulator import MatchManipulator
from helpers.memcache.memcache_webcast_flusher import MemcacheWebcastFlusher
from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

import tba_config

class AdminEventAddWebcast(webapp.RequestHandler):
    """
    Add a webcast to an Event.
    """
    def post(self, event_key_id):

        webcast = dict()
        webcast["type"] = self.request.get("webcast_type")
        webcast["channel"] = self.request.get("webcast_channel")
        if self.request.get("webcast_file"):
            webcast["file"] = self.request.get("webcast_file")

        event = Event.get_by_id(event_key_id)
        if event.webcast:
            webcasts = event.webcast
            webcasts.append(webcast)
            event.webcast_json = json.dumps(webcasts)
        else:
            event.webcast_json = json.dumps([webcast])
        event.dirty = True
        EventManipulator.createOrUpdate(event)

        MemcacheWebcastFlusher.flushEvent(event.key_name)

        self.redirect("/admin/event/" + event.key_name)


class AdminEventCreate(webapp.RequestHandler):
    """
    Create an Event. POSTs to AdminEventEdit.
    """
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_create.html')
        self.response.out.write(template.render(path, {}))


class AdminEventCreateTest(webapp.RequestHandler):
    """
    Create a test event that is happening now.
    """
    def get(self):
        if tba_config.CONFIG["env"] != "prod":
            EventTestCreator.createPastEvent()
            EventTestCreator.createFutureEvent()
            EventTestCreator.createPresentEvent()
            self.redirect("/events/")
        else:
            logging.error("{} tried to create test events in prod! No can do.".format(
                users.get_current_user().email()))
            self.redirect("/admin/")


class AdminEventDelete(webapp.RequestHandler):
    """
    Delete an Event.
    """
    def get(self, event_key_id):
        event = Event.get_by_id(event_key_id)

        template_values = {
            "event": event
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_delete.html')
        self.response.out.write(template.render(path, template_values))

    def post(self, event_key_id):
        logging.warning("Deleting %s at the request of %s / %s" % (
            event_key_id,
            users.get_current_user().user_id(),
            users.get_current_user().email()))

        event = Event.get_by_id(event_key_id)
        
        matches = Match.query(Match.event == event.key).fetch(5000)
        MatchManipulator.delete(matches)

        event_teams = EventTeam.query(EventTeam.event == event.key).fetch(5000)
        EventTeamManipulator.delete(event_teams)

        EventManipulator.delete(event)

        self.redirect("/admin/events?deleted=%s" % event_key_id)


class AdminEventDetail(webapp.RequestHandler):
    """
    Show an Event.
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        event.prepAwardsMatchesTeams()

        template_values = {
            "event": event
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_details.html')
        self.response.out.write(template.render(path, template_values))


class AdminEventEdit(webapp.RequestHandler):
    """
    Edit an Event.
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        
        template_values = {
            "event": event
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_edit.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self, event_key):
        # Note, we don't actually use event_key.

        start_date = None        
        if self.request.get("start_date"):
            start_date = datetime.strptime(self.request.get("start_date"), "%Y-%m-%d")
        
        end_date = None
        if self.request.get("end_date"):
            end_date = datetime.strptime(self.request.get("end_date"), "%Y-%m-%d")
        
        event = Event(
            id = str(self.request.get("year")) + str.lower(str(self.request.get("event_short"))),
            end_date = end_date,
            event_short = self.request.get("event_short"),
            event_type = self.request.get("event_type"),
            location = self.request.get("location"),
            name = self.request.get("name"),
            short_name = self.request.get("short_name"),
            start_date = start_date,
            website = self.request.get("website"),
            year = int(self.request.get("year")),
            official = {"true": True, "false": False}.get(self.request.get("official").lower()),
            facebook_eid = self.request.get("facebook_eid"),
            webcast_json = self.request.get("webcast_json"),
            rankings_json = self.request.get("rankings_json"),
        )
        event = EventManipulator.createOrUpdate(event)
        
        self.redirect("/admin/event/" + event.key_name)


class AdminEventList(webapp.RequestHandler):
    """
    List all Events.
    """
    def get(self):
        events = Event.query().order(Event.year).order(Event.start_date).fetch(10000)
        
        template_values = {
            "events": events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_list.html')
        self.response.out.write(template.render(path, template_values))
