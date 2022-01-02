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
from consts.media_type import MediaType
from consts.media_tag import MediaTag

from datafeeds.datafeed_fms_api import DatafeedFMSAPI
from datafeeds.datafeed_tba import DatafeedTba
from datafeeds.datafeed_resource_library import DatafeedResourceLibrary
from helpers.district_manipulator import DistrictManipulator
from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.match_manipulator import MatchManipulator
from helpers.match_helper import MatchHelper
from helpers.award_manipulator import AwardManipulator
from helpers.media_manipulator import MediaManipulator
from helpers.team_manipulator import TeamManipulator
from helpers.district_team_manipulator import DistrictTeamManipulator
from helpers.robot_manipulator import RobotManipulator
from helpers.event.offseason_event_helper import OffseasonEventHelper
from helpers.suggestions.suggestion_creator import SuggestionCreator

from models.district_team import DistrictTeam
from models.event import Event
from models.event_details import EventDetails
from models.event_team import EventTeam
from models.media import Media
from models.robot import Robot
from models.sitevar import Sitevar
from models.team import Team

from sitevars.website_blacklist import WebsiteBlacklist


class FMSAPIEventAlliancesEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting alliances
    """
    def get(self, when):
        if when == "now":
            events = EventHelper.getEventsWithinADay()
            events = filter(lambda e: e.official, events)
        elif when == "last_day_only":
            events = EventHelper.getEventsWithinADay()
            events = filter(lambda e: e.official and e.ends_today, events)
        else:
            event_keys = Event.query(Event.official == True).filter(Event.year == int(when)).fetch(500, keys_only=True)
            events = ndb.get_multi(event_keys)

        for event in events:
            taskqueue.add(
                queue_name='datafeed',
                url='/tasks/get/fmsapi_event_alliances/' + event.key_name,
                method='GET')

        template_values = {
            'events': events
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_alliances_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class FMSAPIEventAlliancesGet(webapp.RequestHandler):
    """
    Handles updating an event's alliances
    """
    def get(self, event_key):
        df = DatafeedFMSAPI('v2.0', save_response=True)

        event = Event.get_by_id(event_key)

        alliance_selections = df.getEventAlliances(event_key)

        if event and event.remap_teams:
            EventHelper.remapteams_alliances(alliance_selections, event.remap_teams)

        event_details = EventDetails(
            id=event_key,
            alliance_selections=alliance_selections
        )
        EventDetailsManipulator.createOrUpdate(event_details)

        template_values = {'alliance_selections': alliance_selections,
                           'event_name': event_details.key.id()}

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
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

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_rankings_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class FMSAPIEventRankingsGet(webapp.RequestHandler):
    """
    Handles updating an event's rankings
    """
    def get(self, event_key):
        df = DatafeedFMSAPI('v2.0', save_response=True)

        event = Event.get_by_id(event_key)

        rankings, rankings2 = df.getEventRankings(event_key)

        if event and event.remap_teams:
            EventHelper.remapteams_rankings(rankings, event.remap_teams)
            EventHelper.remapteams_rankings2(rankings2, event.remap_teams)

        event_details = EventDetails(
            id=event_key,
            rankings=rankings,
            rankings2=rankings2
        )
        EventDetailsManipulator.createOrUpdate(event_details)

        template_values = {'rankings': rankings,
                           'event_name': event_details.key.id()}

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
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

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_matches_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class FMSAPIMatchesGet(webapp.RequestHandler):
    """
    Handles updating matches
    """
    def get(self, event_key):
        df = DatafeedFMSAPI('v2.0', save_response=True)
        event = Event.get_by_id(event_key)

        matches = MatchHelper.delete_invalid_matches(
            df.getMatches(event_key),
            Event.get_by_id(event_key)
        )

        if event and event.remap_teams:
            EventHelper.remapteams_matches(matches, event.remap_teams)

        new_matches = MatchManipulator.createOrUpdate(matches)

        template_values = {
            'matches': new_matches,
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_matches_get.html')
            self.response.out.write(template.render(path, template_values))



class DistrictListGet(webapp.RequestHandler):
    """
    Fetch one year of districts only from FMS API
    """
    def get(self, year):
        df = DatafeedFMSAPI('v2.0')
        fmsapi_districts = df.getDistrictList(year)
        districts = DistrictManipulator.createOrUpdate(fmsapi_districts)

        template_values = {
            "districts": districts,
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/fms_district_list_get.html')
            self.response.out.write(template.render(path, template_values))


class DistrictRankingsGet(webapp.RequestHandler):
    """
    Fetch district rankings from FIRST
    This data does not have full pre-event point breakdowns, but it does contain
    things like CMP advancement
    """
    def get(self, district_key):
        df = DatafeedFMSAPI('v2.0')

        district_with_rankings = df.getDistrictRankings(district_key)
        districts = []
        if district_with_rankings:
            districts = DistrictManipulator.createOrUpdate(district_with_rankings)

        template_values = {
            "districts": [districts],
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/fms_district_list_get.html')
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

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
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

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/tba_videos_get.html')
            self.response.out.write(template.render(path, template_values))


class HallOfFameTeamsGet(webapp.RequestHandler):
    """
    Handles scraping the list of Hall of Fame teams from FIRST resource library.
    """
    def get(self):
        df = DatafeedResourceLibrary()

        teams = df.getHallOfFameTeams()
        if teams:
            media_to_update = []
            for team in teams:
                team_reference = Media.create_reference('team', team['team_id'])

                video_foreign_key = team['video']
                if video_foreign_key:
                    media_to_update.append(Media(id=Media.render_key_name(MediaType.YOUTUBE_VIDEO, video_foreign_key),
                                                 media_type_enum=MediaType.YOUTUBE_VIDEO,
                                                 media_tag_enum=[MediaTag.CHAIRMANS_VIDEO],
                                                 references=[team_reference],
                                                 year=team['year'],
                                                 foreign_key=video_foreign_key))

                presentation_foreign_key = team['presentation']
                if presentation_foreign_key:
                    media_to_update.append(Media(id=Media.render_key_name(MediaType.YOUTUBE_VIDEO, presentation_foreign_key),
                                                 media_type_enum=MediaType.YOUTUBE_VIDEO,
                                                 media_tag_enum=[MediaTag.CHAIRMANS_PRESENTATION],
                                                 references=[team_reference],
                                                 year=team['year'],
                                                 foreign_key=presentation_foreign_key))

                essay_foreign_key = team['essay']
                if essay_foreign_key:
                    media_to_update.append(Media(id=Media.render_key_name(MediaType.EXTERNAL_LINK, essay_foreign_key),
                                                 media_type_enum=MediaType.EXTERNAL_LINK,
                                                 media_tag_enum=[MediaTag.CHAIRMANS_ESSAY],
                                                 references=[team_reference],
                                                 year=team['year'],
                                                 foreign_key=essay_foreign_key))

            MediaManipulator.createOrUpdate(media_to_update)
        else:
            logging.info("No Hall of Fame teams found")
            teams = []

        template_values = {
            'teams': teams,
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/hall_of_fame_teams_get.html')
            self.response.out.write(template.render(path, template_values))


class TeamBlacklistWebsiteDo(webapp.RequestHandler):
    """
    Blacklist the current website for a team
    """
    def get(self, key_name):
        team = Team.get_by_id(key_name)

        if team.website:
            WebsiteBlacklist.blacklist(team.website)

        self.redirect('/backend-tasks/get/team_details/{}'.format(key_name))
