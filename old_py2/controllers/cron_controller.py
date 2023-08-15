import datetime
import logging
import os
import json

from google.appengine.api import taskqueue

from google.appengine.ext import ndb

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from consts.event_type import EventType

from controllers.api.api_status_controller import ApiStatusController
from database.district_query import DistrictsInYearQuery
from database.event_query import DistrictEventsQuery, EventQuery
from database.match_query import EventMatchesQuery
from database.team_query import DistrictTeamsQuery
from helpers.award_manipulator import AwardManipulator
from helpers.bluezone_helper import BlueZoneHelper
from helpers.district_helper import DistrictHelper
from helpers.district_manipulator import DistrictManipulator
from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.event_insights_helper import EventInsightsHelper
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.event_team_status_helper import EventTeamStatusHelper
from helpers.event_team_repairer import EventTeamRepairer
from helpers.event_team_updater import EventTeamUpdater
from helpers.firebase.firebase_pusher import FirebasePusher
from helpers.insights_helper import InsightsHelper
from helpers.match_helper import MatchHelper
from helpers.match_time_prediction_helper import MatchTimePredictionHelper
from helpers.matchstats_helper import MatchstatsHelper
from helpers.notification_helper import NotificationHelper
from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from helpers.prediction_helper import PredictionHelper

from helpers.insight_manipulator import InsightManipulator
from helpers.suggestions.suggestion_fetcher import SuggestionFetcher
from helpers.team_manipulator import TeamManipulator
from helpers.match_manipulator import MatchManipulator
from models.district import District
from models.event import Event
from models.event_details import EventDetails
from models.event_team import EventTeam
from models.match import Match
from models.sitevar import Sitevar
from models.suggestion import Suggestion
from models.team import Team


class EventShortNameCalcEnqueue(webapp.RequestHandler):
    """
    Enqueues Event short_name computation for official events
    """
    def get(self, year):
        event_keys = Event.query(Event.official == True, Event.year == int(year)).fetch(200, keys_only=True)
        events = ndb.get_multi(event_keys)

        for event in events:
            taskqueue.add(
                url='/tasks/math/do/event_short_name_calc_do/{}'.format(event.key.id()),
                method='GET')

        template_values = {'events': events}
        path = os.path.join(os.path.dirname(__file__), '../templates/math/event_short_name_calc_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class EventShortNameCalcDo(webapp.RequestHandler):
    """
    Computes Event short_name
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        event.short_name = EventHelper.getShortName(event.name)
        EventManipulator.createOrUpdate(event)

        template_values = {'event': event}
        path = os.path.join(os.path.dirname(__file__), '../templates/math/event_short_name_calc_do.html')
        self.response.out.write(template.render(path, template_values))


class EventTeamRepairDo(webapp.RequestHandler):
    """
    Repair broken EventTeams.
    """
    def get(self):
        event_teams_keys = EventTeam.query(EventTeam.year == None).fetch(keys_only=True)
        event_teams = ndb.get_multi(event_teams_keys)

        event_teams = EventTeamRepairer.repair(event_teams)
        event_teams = EventTeamManipulator.createOrUpdate(event_teams)

        # sigh. -gregmarra
        if type(event_teams) == EventTeam:
            event_teams = [event_teams]

        template_values = {
            'event_teams': event_teams,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/eventteam_repair_do.html')
        self.response.out.write(template.render(path, template_values))


class FinalMatchesRepairDo(webapp.RequestHandler):
    """
    Repairs zero-indexed final matches
    """
    def get(self, year):
        year_event_keys = Event.query(Event.year == int(year)).fetch(1000, keys_only=True)

        final_match_keys = []
        for event_key in year_event_keys:
            final_match_keys.extend(Match.query(Match.event == event_key, Match.comp_level == 'f').fetch(100, keys_only=True))

        match_keys_to_repair = []
        for match_key in final_match_keys:
            key_name = match_key.id()
            if '_f0m' in key_name:
                match_keys_to_repair.append(match_key)

        deleted_keys = []
        matches_to_repair = ndb.get_multi(match_keys_to_repair)
        for match in matches_to_repair:
            deleted_keys.append(match.key)

            event = ndb.get_multi([match.event])[0]
            match.set_number = 1
            match.key = ndb.Key(Match, Match.render_key_name(
                event.key.id(),
                match.comp_level,
                match.set_number,
                match.match_number))

        MatchManipulator.createOrUpdate(matches_to_repair)
        MatchManipulator.delete_keys(deleted_keys)

        template_values = {'deleted_keys': deleted_keys,
                           'new_matches': matches_to_repair}

        path = os.path.join(os.path.dirname(__file__), '../templates/math/final_matches_repair_do.html')
        self.response.out.write(template.render(path, template_values))


class YearInsightsEnqueue(webapp.RequestHandler):
    """
    Enqueues Insights calculation of a given kind for a given year
    """
    def get(self, kind, year):
        taskqueue.add(
            target='backend-tasks-b2',
            url='/backend-tasks-b2/math/do/insights/{}/{}'.format(kind, year),
            method='GET')

        template_values = {
            'kind': kind,
            'year': year
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/year_insights_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class YearInsightsDo(webapp.RequestHandler):
    """
    Calculates insights of a given kind for a given year.
    Calculations of a given kind should reuse items fetched from the datastore.
    """

    def get(self, kind, year):
        year = int(year)

        insights = None
        if kind == 'matches':
            insights = InsightsHelper.doMatchInsights(year)
        elif kind == 'awards':
            insights = InsightsHelper.doAwardInsights(year)
        elif kind == 'predictions':
            insights = InsightsHelper.doPredictionInsights(year)

        if insights != None:
            InsightManipulator.createOrUpdate(insights)

        template_values = {
            'insights': insights,
            'year': year,
            'kind': kind,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/year_insights_do.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        self.get()


class OverallInsightsEnqueue(webapp.RequestHandler):
    """
    Enqueues Overall Insights calculation for a given kind.
    """
    def get(self, kind):
        taskqueue.add(
            target='backend-tasks-b2',
            url='/backend-tasks-b2/math/do/overallinsights/{}'.format(kind),
            method='GET')

        template_values = {
            'kind': kind,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/overall_insights_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class OverallInsightsDo(webapp.RequestHandler):
    """
    Calculates overall insights of a given kind.
    Calculations of a given kind should reuse items fetched from the datastore.
    """

    def get(self, kind):
        insights = None
        if kind == 'matches':
            insights = InsightsHelper.doOverallMatchInsights()
        elif kind == 'awards':
            insights = InsightsHelper.doOverallAwardInsights()

        if insights != None:
            InsightManipulator.createOrUpdate(insights)

        template_values = {
            'insights': insights,
            'kind': kind,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/overall_insights_do.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        self.get()


class UpcomingNotificationDo(webapp.RequestHandler):
    """
    Sends out notifications for upcoming matches
    """
    def get(self):
        live_events = EventHelper.getEventsWithinADay()
        NotificationHelper.send_upcoming_matches(live_events)


class BlueZoneUpdateDo(webapp.RequestHandler):
    """
    Update the current "best match"
    """
    def get(self):
        live_events = EventHelper.getEventsWithinADay()
        try:
            BlueZoneHelper.update_bluezone(live_events)
        except Exception, e:
            logging.error("BlueZone update failed")
            logging.exception(e)
