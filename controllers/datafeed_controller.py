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
from datafeeds.datafeed_first_elasticsearch import DatafeedFIRSTElasticSearch
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

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_awards_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class FMSAPIAwardsGet(webapp.RequestHandler):
    """
    Handles updating awards
    """
    def get(self, event_key):
        datafeed = DatafeedFMSAPI('v2.0', save_response=True)

        event = Event.get_by_id(event_key)
        awards = datafeed.getAwards(event)

        if event and event.remap_teams:
            EventHelper.remapteams_awards(awards, event.remap_teams)

        new_awards = AwardManipulator.createOrUpdate(awards)

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

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
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

        matches = MatchHelper.deleteInvalidMatches(
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


class TeamDetailsGet(webapp.RequestHandler):
    """
    Fetches team details
    FMSAPI should be trusted over FIRSTElasticSearch
    """
    def get(self, key_name):
        existing_team = Team.get_by_id(key_name)

        fms_df = DatafeedFMSAPI('v2.0')
        df2 = DatafeedFIRSTElasticSearch()
        year = datetime.date.today().year
        fms_details = fms_df.getTeamDetails(year, key_name)

        if fms_details:
            team, district_team, robot = fms_details[0]
        else:
            team = None
            district_team = None
            robot = None

        if team:
            team = TeamManipulator.mergeModels(team, df2.getTeamDetails(existing_team))
        else:
            team = df2.getTeamDetails(existing_team)

        if team:
            team = TeamManipulator.createOrUpdate(team)

        # Clean up junk district teams
        # https://www.facebook.com/groups/moardata/permalink/1310068625680096/
        dt_keys = DistrictTeam.query(
            DistrictTeam.team == existing_team.key,
            DistrictTeam.year == year).fetch(keys_only=True)
        keys_to_delete = set()
        for dt_key in dt_keys:
            if not district_team or dt_key.id() != district_team.key.id():
                keys_to_delete.add(dt_key)
        DistrictTeamManipulator.delete_keys(keys_to_delete)

        if district_team:
            district_team = DistrictTeamManipulator.createOrUpdate(district_team)

        if robot:
            robot = RobotManipulator.createOrUpdate(robot)

        template_values = {
            'key_name': key_name,
            'team': team,
            'success': team is not None,
            'district': district_team,
            'robot': robot,
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_team_details_get.html')
            self.response.out.write(template.render(path, template_values))


class TeamAvatarGet(webapp.RequestHandler):
    """
    Fetches team avatar
    Doesn't currently use FIRSTElasticSearch
    """

    def get(self, key_name):
        fms_df = DatafeedFMSAPI('v2.0')
        year = datetime.date.today().year
        team = Team.get_by_id(key_name)

        avatar, keys_to_delete = fms_df.getTeamAvatar(year, key_name)

        if avatar:
            MediaManipulator.createOrUpdate(avatar)

        MediaManipulator.delete_keys(keys_to_delete)

        template_values = {
            'key_name': key_name,
            'team': team,
            'success': avatar is not None,
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_team_avatar_get.html')
            self.response.out.write(template.render(path, template_values))


class EventListCurrentEnqueue(webapp.RequestHandler):
    """
    Enqueue fetching events for years between current year and max year
    """
    def get(self):
        sv = Sitevar.get_by_id('apistatus')
        current_year = sv.contents['current_season']
        max_year = sv.contents['max_season']
        years = range(current_year, max_year + 1)
        for year in years:
            taskqueue.add(
                queue_name='datafeed',
                target='backend-tasks',
                url='/backend-tasks/get/event_list/%d' % year,
                method='GET'
            )

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            self.response.out.write("Enqueued fetching events for {}".format(years))


class EventListEnqueue(webapp.RequestHandler):
    """
    Handles enqueing fetching a year's worth of events from FMSAPI
    """
    def get(self, year):

        taskqueue.add(
            queue_name='datafeed',
            target='backend-tasks',
            url='/backend-tasks/get/event_list/' + year,
            method='GET'
        )

        template_values = {
            'year': year,
            'event_count': year
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_events_details_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class EventListGet(webapp.RequestHandler):
    """
    Fetch all events for a given year via the FRC Events API.
    """
    def get(self, year):
        df_config = Sitevar.get_or_insert('event_list_datafeed_config')
        df = DatafeedFMSAPI('v2.0')
        df2 = DatafeedFIRSTElasticSearch()

        fmsapi_events, event_list_districts = df.getEventList(year)
        if df_config.contents.get('enable_es') == True:
            elasticsearch_events = df2.getEventList(year)
        else:
            elasticsearch_events = []

        # All regular-season events can be inserted without any work involved.
        # We need to de-duplicate offseason events from the FRC Events API with a different code than the TBA event code
        fmsapi_events_offseason = [e for e in fmsapi_events if e.is_offseason]
        event_keys_to_put = set([e.key_name for e in fmsapi_events]) - set(
            [e.key_name for e in fmsapi_events_offseason])
        events_to_put = [e for e in fmsapi_events if e.key_name in event_keys_to_put]

        matched_offseason_events, new_offseason_events = \
            OffseasonEventHelper.categorize_offseasons(int(year), fmsapi_events_offseason)

        # For all matched offseason events, make sure the FIRST code matches the TBA FIRST code
        for tba_event, first_event in matched_offseason_events:
            tba_event.first_code = first_event.event_short
            events_to_put.append(tba_event)  # Update TBA events - discard the FIRST event

        # For all new offseason events we can't automatically match, create suggestions
        SuggestionCreator.createDummyOffseasonSuggestions(new_offseason_events)

        merged_events = EventManipulator.mergeModels(
            list(events_to_put),
            elasticsearch_events) if elasticsearch_events else list(
                events_to_put)
        events = EventManipulator.createOrUpdate(merged_events) or []

        fmsapi_districts = df.getDistrictList(year)
        merged_districts = DistrictManipulator.mergeModels(fmsapi_districts, event_list_districts)
        if merged_districts:
            districts = DistrictManipulator.createOrUpdate(merged_districts)
        else:
            districts = []

        # Fetch event details for each event
        for event in events:
            taskqueue.add(
                queue_name='datafeed',
                target='backend-tasks',
                url='/backend-tasks/get/event_details/'+event.key_name,
                method='GET'
            )

        template_values = {
            "events": events,
            "districts": districts,
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/fms_event_list_get.html')
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


class EventDetailsEnqueue(webapp.RequestHandler):
    """
    Handlers enqueueing fetching event details, event teams, and team details
    """
    def get(self, event_key):
        taskqueue.add(
            queue_name='datafeed',
            target='backend-tasks',
            url='/backend-tasks/get/event_details/'+event_key,
            method='GET')

        template_values = {
            'event_key': event_key
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/fmsapi_eventteams_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class EventDetailsGet(webapp.RequestHandler):
    """
    Fetch event details, event teams, and team details
    FMSAPI should be trusted over FIRSTElasticSearch
    """
    def get(self, event_key):
        df = DatafeedFMSAPI('v2.0')
        df2 = DatafeedFIRSTElasticSearch()

        event = Event.get_by_id(event_key)

        # Update event
        fmsapi_events, fmsapi_districts = df.getEventDetails(event_key)
        elasticsearch_events = df2.getEventDetails(event)
        updated_event = EventManipulator.mergeModels(
            fmsapi_events,
            elasticsearch_events)
        if updated_event:
            event = EventManipulator.createOrUpdate(updated_event)
        DistrictManipulator.createOrUpdate(fmsapi_districts)

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
        if teams and event.year == tba_config.MAX_YEAR:  # Only update from latest year
            teams = TeamManipulator.createOrUpdate(teams)
        district_teams = DistrictTeamManipulator.createOrUpdate(district_teams)
        robots = RobotManipulator.createOrUpdate(robots)

        if not teams:
            # No teams found registered for this event
            teams = []
        if type(teams) is not list:
            teams = [teams]

        # Build EventTeams
        cmp_hack_sitevar = Sitevar.get_or_insert('cmp_registration_hacks')
        events_without_eventteams = cmp_hack_sitevar.contents.get('skip_eventteams', []) \
            if cmp_hack_sitevar else []
        skip_eventteams = event_key in events_without_eventteams
        event_teams = [EventTeam(
            id=event.key_name + "_" + team.key_name,
            event=event.key,
            team=team.key,
            year=event.year)
            for team in teams] if not skip_eventteams else []

        # Delete eventteams of teams that are no longer registered
        if event_teams and not skip_eventteams:
            existing_event_team_keys = set(EventTeam.query(EventTeam.event == event.key).fetch(1000, keys_only=True))
            event_team_keys = set([et.key for et in event_teams])
            et_keys_to_delete = existing_event_team_keys.difference(event_team_keys)
            EventTeamManipulator.delete_keys(et_keys_to_delete)

            event_teams = EventTeamManipulator.createOrUpdate(event_teams)
        if type(event_teams) is not list:
            event_teams = [event_teams]

        if event.year in {2018, 2019, 2020}:
            avatars, keys_to_delete = df.getEventTeamAvatars(event.key_name)
            if avatars:
                MediaManipulator.createOrUpdate(avatars)
            MediaManipulator.delete_keys(keys_to_delete)

        template_values = {
            'event': event,
            'event_teams': event_teams,
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_details_get.html')
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
