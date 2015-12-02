import logging
import os
import datetime
import tba_config
import time
import json

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from consts.event_type import EventType

from datafeeds.datafeed_fms_api import DatafeedFMSAPI
from datafeeds.datafeed_first_elasticsearch import DatafeedFIRSTElasticSearch
from datafeeds.datafeed_tba import DatafeedTba

from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.match_manipulator import MatchManipulator
from helpers.match_helper import MatchHelper
from helpers.award_manipulator import AwardManipulator
from helpers.team_manipulator import TeamManipulator
from helpers.district_team_manipulator import DistrictTeamManipulator
from helpers.robot_manipulator import RobotManipulator

from models.district_team import DistrictTeam
from models.event import Event
from models.event_team import EventTeam
from models.robot import Robot
from models.team import Team


class FMSAPIAwardsEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting awards
    """
    def get(self, when):
        if when == "now":
            events = EventHelper.getEventsWithinADay()
            events = filter(lambda e: e.official, events)
        else:
            event_keys = Event.query(Event.official == True).filter(Event.year == int(when)).fetch(500, keys_only=True)
            events = ndb.get_multi(event_keys)

        for event in events:
            taskqueue.add(
                queue_name='datafeed',
                url='/tasks/get/fmsapi_awards/%s' % (event.key_name),
                method='GET')
        template_values = {
            'events': events,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_awards_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class FMSAPIAwardsGet(webapp.RequestHandler):
    """
    Handles updating awards
    """
    def get(self, event_key):
        datafeed = DatafeedFMSAPI('v2.0')

        event = Event.get_by_id(event_key)
        new_awards = AwardManipulator.createOrUpdate(datafeed.getAwards(event))

        if new_awards is None:
            new_awards = []
        elif type(new_awards) != list:
            new_awards = [new_awards]

        # create EventTeams
        team_ids = set()
        for award in new_awards:
            for team in award.team_list:
                team_ids.add(team.id())
        teams = TeamManipulator.createOrUpdate([Team(
            id=team_id,
            team_number=int(team_id[3:]))
            for team_id in team_ids])
        if teams:
            if type(teams) is not list:
                teams = [teams]
            event_teams = EventTeamManipulator.createOrUpdate([EventTeam(
                id=event_key + "_" + team.key.id(),
                event=event.key,
                team=team.key,
                year=event.year)
                for team in teams])

        template_values = {
            'awards': new_awards,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_awards_get.html')
        self.response.out.write(template.render(path, template_values))


class FMSAPIEventAlliancesEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting alliances
    """
    def get(self, when):
        if when == "now":
            events = EventHelper.getEventsWithinADay()
            events = filter(lambda e: e.official, events)
        else:
            event_keys = Event.query(Event.official == True).filter(Event.year == int(when)).fetch(500, keys_only=True)
            events = ndb.get_multi(event_keys)

        for event in events:
            taskqueue.add(
                queue_name='datafeed',
                url='/tasks/get/fmsapi_event_alliances/' + event.key_name,
                method='GET')

        template_values = {
            'events': events,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_alliances_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class FMSAPIEventAlliancesGet(webapp.RequestHandler):
    """
    Handles updating an event's alliances
    """
    def get(self, event_key):
        df = DatafeedFMSAPI('v2.0')

        event = Event.get_by_id(event_key)

        if event.event_type_enum == EventType.CMP_FINALS:
            logging.info("Skipping Einstein alliance selections")
            return

        alliance_selections = df.getEventAlliances(event_key)
        if alliance_selections and event.alliance_selections != alliance_selections:
            event.alliance_selections_json = json.dumps(alliance_selections)
            event._alliance_selections = None
            event.dirty = True

        EventManipulator.createOrUpdate(event)

        template_values = {'alliance_selections': alliance_selections,
                           'event_name': event.key_name}

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_alliances_get.html')
        self.response.out.write(template.render(path, template_values))


class FMSAPIEventRankingsEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting rankings
    """
    def get(self, when):
        if when == "now":
            events = EventHelper.getEventsWithinADay()
            events = filter(lambda e: e.official, events)
        else:
            event_keys = Event.query(Event.official == True).filter(Event.year == int(when)).fetch(500, keys_only=True)
            events = ndb.get_multi(event_keys)

        for event in events:
            taskqueue.add(
                queue_name='datafeed',
                url='/tasks/get/fmsapi_event_rankings/' + event.key_name,
                method='GET')

        template_values = {
            'events': events,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_rankings_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class FMSAPIEventRankingsGet(webapp.RequestHandler):
    """
    Handles updating an event's rankings
    """
    def get(self, event_key):
        df = DatafeedFMSAPI('v2.0')

        rankings = df.getEventRankings(event_key)

        event = Event.get_by_id(event_key)
        if rankings and event.rankings_json != json.dumps(rankings):
            event.rankings_json = json.dumps(rankings)
            event.dirty = True

        EventManipulator.createOrUpdate(event)

        template_values = {'rankings': rankings,
                           'event_name': event.key_name}

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_rankings_get.html')
        self.response.out.write(template.render(path, template_values))


class FMSAPIMatchesEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting match results
    """
    def get(self, when):
        if when == "now":
            events = EventHelper.getEventsWithinADay()
            events = filter(lambda e: e.official, events)
        else:
            event_keys = Event.query(Event.official == True).filter(Event.year == int(when)).fetch(500, keys_only=True)
            events = ndb.get_multi(event_keys)

        for event in events:
            taskqueue.add(
                queue_name='datafeed',
                url='/tasks/get/fmsapi_matches/' + event.key_name,
                method='GET')

        template_values = {
            'events': events,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_matches_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class FMSAPIMatchesGet(webapp.RequestHandler):
    """
    Handles updating matches
    """
    def get(self, event_key):
        df = DatafeedFMSAPI('v2.0')

        new_matches = MatchManipulator.createOrUpdate(df.getMatches(event_key))

        template_values = {
            'matches': new_matches,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_matches_get.html')
        self.response.out.write(template.render(path, template_values))

# TODO: Currently unused

# class TeamDetailsEnqueue(webapp.RequestHandler):
#     """
#     Handles enqueing updates to individual teams
#     """
#     def get(self):
#         offset = int(self.request.get("offset", 0))

#         team_keys = Team.query().fetch(1000, offset=int(offset), keys_only=True)
#         teams = ndb.get_multi(team_keys)
#         for team in teams:
#             taskqueue.add(
#                 queue_name='frc-api',
#                 url='/tasks/get/fmsapi_team_details/' + team.key_name,
#                 method='GET')

#         # FIXME omg we're just writing out? -gregmarra 2012 Aug 26
#         self.response.out.write("%s team gets have been enqueued offset from %s.<br />" % (len(teams), offset))
#         self.response.out.write("Reload with ?offset=%s to enqueue more." % (offset + len(teams)))


# class TeamDetailsRollingEnqueue(webapp.RequestHandler):
#     """
#     Handles enqueing updates to individual teams
#     Enqueues a certain fraction of teams so that all teams will get updated
#     every PERIOD days.
#     """
#     PERIOD = 14  # a particular team will be updated every PERIOD days

#     def get(self):
#         now_epoch = time.mktime(datetime.datetime.now().timetuple())
#         bucket_num = int((now_epoch / (60 * 60 * 24)) % self.PERIOD)

#         highest_team_key = Team.query().order(-Team.team_number).fetch(1, keys_only=True)[0]
#         highest_team_num = int(highest_team_key.id()[3:])
#         bucket_size = int(highest_team_num / (self.PERIOD)) + 1

#         min_team = bucket_num * bucket_size
#         max_team = min_team + bucket_size
#         team_keys = Team.query(Team.team_number >= min_team, Team.team_number < max_team).fetch(1000, keys_only=True)

#         teams = ndb.get_multi(team_keys)
#         for team in teams:
#             taskqueue.add(
#                 queue_name='datafeed',
#                 url='/tasks/get/fmsapi_team_details/' + team.key_name,
#                 method='GET')

#         # FIXME omg we're just writing out? -fangeugene 2013 Nov 6
#         self.response.out.write("Bucket number {} out of {}<br>".format(bucket_num, self.PERIOD))
#         self.response.out.write("{} team gets have been enqueued in the interval [{}, {}).".format(len(teams), min_team, max_team))


# class TeamDetailsGet(webapp.RequestHandler):
#     """
#     Requests team details from FMS API and imports the data
#     """
#     def get(self, key_name):
#         fms_df = DatafeedFMSAPI('v2.0')
#         fms_details = fms_df.getTeamDetails(date.today().year, key_name)

#         if fms_details:
#             team, district_team, robot = fms_details
#         else:
#             fms_team = None
#             district_team = None
#             robot = None

#         if team:
#             team = TeamManipulator.createorUpdate(team)

#         if district_team:
#             district_team = DistrictTeamManipulator.createOrUpdate(district_team)

#         if robot:
#             robot = RobotManipulator.createOrUpdate(robot)

#         template_values = {
#             'key_name': key_name,
#             'team': team,
#             'success': success,
#             'district': district_team,
#             'robot': robot,
#         }

#         path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_team_details_get.html')
#         self.response.out.write(template.render(path, template_values))


class EventListEnqueue(webapp.RequestHandler):
    """
    Handles enqueing fetching a year's worth of events from FMSAPI
    """
    def get(self, year):

        taskqueue.add(
            queue_name='datafeed',
            url='/tasks/get/event_list/' + year,
            method='GET'
        )

        template_values = {
            'year': year,
            'event_count': year
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_events_details_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class EventListGet(webapp.RequestHandler):
    """
    Fetch one year of events
    FMSAPI should be trusted over FIRSTElasticSearch
    """
    def get(self, year):
        df = DatafeedFMSAPI('v2.0')
        df2 = DatafeedFIRSTElasticSearch()

        merged_events = EventManipulator.mergeModels(df.getEventList(year), df2.getEventList(year))
        events = EventManipulator.createOrUpdate(merged_events)

        # Fetch EventTeams for each event
        for event in events:
            taskqueue.add(
                queue_name='datafeed',
                url='/tasks/get/eventteams/'+event.key_name,
                method='GET'
            )

        template_values = {
            "events": events
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/fms_event_list_get.html')
        self.response.out.write(template.render(path, template_values))


class EventTeamsEnqueue(webapp.RequestHandler):
    """
    Handlers enqueueing fetching a list of teams attending an event
    """
    def get(self, event_key):
        taskqueue.add(
            queue_name='datafeed',
            url='/tasks/get/eventteams/'+event_key,
            method='GET')

        template_values = {
            'event_key': event_key
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/fmsapi_eventteams_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class EventTeamsGet(webapp.RequestHandler):
    """
    Fetch list of teams attending a single event
    FMSAPI should be trusted over FIRSTElasticSearch
    """
    def get(self, event_key):
        df = DatafeedFMSAPI('v2.0')
        df2 = DatafeedFIRSTElasticSearch()

        event = Event.get_by_id(event_key)

        models = df.getEventTeams(event_key)
        teams = []
        district_teams = []
        robots = []
        for group in models:
            # models is a list of tuples (team, districtTeam, robot)
            if isinstance(group[0], Team):
                teams.append(group[0])
            if isinstance(group[1], DistrictTeam):
                district_teams.append(group[1])
            if isinstance(group[2], Robot):
                robots.append(group[2])

        # Merge teams
        teams = TeamManipulator.mergeModels(teams, df2.getEventTeams(event))

        # Write new models
        teams = TeamManipulator.createOrUpdate(teams)
        district_teams = DistrictTeamManipulator.createOrUpdate(district_teams)
        robots = RobotManipulator.createOrUpdate(robots)

        if not teams:
            # No teams found registered for this event
            teams = []

        # Build EventTeams
        event_teams = [EventTeam(
            id=event.key_name + "_" + team.key_name,
            event=event.key,
            team=team.key,
            year=event.year)
            for team in teams]

        # Delete eventteams of teams that are no longer registered
        if event_teams != []:
            existing_event_team_keys = set(EventTeam.query(EventTeam.event == event.key).fetch(1000, keys_only=True))
            event_team_keys = set([et.key for et in event_teams])
            et_keys_to_delete = existing_event_team_keys.difference(event_team_keys)
            EventTeamManipulator.delete_keys(et_keys_to_delete)

        event_teams = EventTeamManipulator.createOrUpdate(event_teams)
        if type(event_teams) is not list:
            event_teams = [event_teams]

        template_values = {
            'event': event,
            'event_teams': event_teams,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_details_get.html')
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
            for match in event.matches:
                if match.tba_videos != match_filetypes.get(match.key_name, []):
                    match.tba_videos = match_filetypes.get(match.key_name, [])
                    match.dirty = True
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
