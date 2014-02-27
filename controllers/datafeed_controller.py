import logging
import os
import datetime
import time
import json

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from consts.event_type import EventType

from datafeeds.datafeed_fms import DatafeedFms
from datafeeds.datafeed_tba import DatafeedTba
from datafeeds.datafeed_usfirst import DatafeedUsfirst
from datafeeds.datafeed_usfirst_legacy import DatafeedUsfirstLegacy
from datafeeds.datafeed_offseason import DatafeedOffseason
from datafeeds.datafeed_twitter import DatafeedTwitter

from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.match_manipulator import MatchManipulator
from helpers.match_helper import MatchHelper
from helpers.award_manipulator import AwardManipulator
from helpers.team_manipulator import TeamManipulator

from models.event import Event
from models.event_team import EventTeam
from models.team import Team

from helpers.firebase.firebase_pusher import FirebasePusher


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


class UsfirstEventDetailsEnqueue(webapp.RequestHandler):
    """
    Handles enqueing updates to individual USFIRST events.
    """
    def get(self, year):
        event_keys = Event.query(Event.first_eid != None, Event.year == int(year)).fetch(200, keys_only=True)
        events = ndb.get_multi(event_keys)

        for event in events:
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_event_details/%s/%s' % (year, event.first_eid),
                method='GET')

        template_values = {
            'event_count': len(events),
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
        df = DatafeedUsfirst()
        df_legacy = DatafeedUsfirstLegacy()

        event = df.getEventDetails(first_eid)
        if not event:
            logging.warning("getEventDetails with DatafeedUsfirst for event id {} failed. Retrying with DatafeedUsfirstLegacy.".format(first_eid))
            event = df_legacy.getEventDetails(int(year), first_eid)
        event = EventManipulator.createOrUpdate(event)

        teams = df.getEventTeams(int(year), first_eid)
        if not teams:
            logging.warning("getEventTeams with DatafeedUsfirst for event id {} failed. Retrying with DatafeedUsfirstLegacy.".format(first_eid))
            teams = df_legacy.getEventTeams(int(year), first_eid)
            if not teams:
                logging.warning("getEventTeams with DatafeedUsfirstLegacy for event id {} failed.".format(first_eid))
                teams = []

        teams = TeamManipulator.createOrUpdate(teams)

        if teams:
            if type(teams) is not list:
                teams = [teams]

            event_teams = [EventTeam(
                id=event.key.id() + "_" + team.key.id(),
                event=event.key,
                team=team.key,
                year=event.year)
                for team in teams]

            # Delete eventteams of teams that unregister from an event
            if event.future:
                existing_event_team_keys = set(EventTeam.query(EventTeam.event == event.key).fetch(1000, keys_only=True))
                event_team_keys = set([et.key for et in event_teams])
                et_keys_to_delete = existing_event_team_keys.difference(event_team_keys)
                ndb.delete_multi(et_keys_to_delete)

            event_teams = EventTeamManipulator.createOrUpdate(event_teams)
            if type(event_teams) is not list:
                event_teams = [event_teams]
        else:
            event_teams = []

        template_values = {
            'event': event,
            'event_teams': event_teams,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_event_details_get.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstAwardsEnqueue(webapp.RequestHandler):
    """
    Handles enqueing getting awards for USFIRST events.
    """
    def get(self, when):
        if when == "now":
            events = EventHelper.getEventsWithinADay()
        else:
            event_keys = Event.query(Event.official == True).filter(Event.year == int(when)).fetch(500, keys_only=True)
            events = ndb.get_multi(event_keys)

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
    Also creates EventTeams.
    """
    def get(self, event_key):
        datafeed = DatafeedUsfirst()

        event = Event.get_by_id(event_key)
        new_awards = AwardManipulator.createOrUpdate(datafeed.getEventAwards(event))
        if type(new_awards) != list:
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
        if when == "now":
            events = EventHelper.getEventsWithinADay()
        else:
            event_keys = Event.query(Event.official == True).filter(Event.year == int(when)).fetch(500, keys_only=True)
            events = ndb.get_multi(event_keys)

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
        try:
            FirebasePusher.updated_event(event.key_name)
        except:
            logging.warning("Enqueuing Firebase push failed!")

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
        if when == "now":
            events = EventHelper.getEventsWithinADay()
        else:
            event_keys = Event.query(Event.official == True).filter(Event.year == int(when)).fetch(500, keys_only=True)
            events = ndb.get_multi(event_keys)

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
        if event.rankings_json != json.dumps(rankings):
            event.rankings_json = json.dumps(rankings)
            event.dirty = True

        EventManipulator.createOrUpdate(event)

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

        team_keys = Team.query().fetch(1000, offset=int(offset), keys_only=True)
        teams = ndb.get_multi(team_keys)
        for team in teams:
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_team_details/' + team.key_name,
                method='GET')

        # FIXME omg we're just writing out? -gregmarra 2012 Aug 26
        self.response.out.write("%s team gets have been enqueued offset from %s.<br />" % (len(teams), offset))
        self.response.out.write("Reload with ?offset=%s to enqueue more." % (offset + len(teams)))


class UsfirstTeamDetailsRollingEnqueue(webapp.RequestHandler):
    """
    Handles enqueing updates to individual USFIRST teams.
    Enqueues a certain fraction of teams so that all teams will get updated
    every PERIOD days.
    """
    PERIOD = 14  # a particular team will be updated every PERIOD days

    def get(self):
        now_epoch = time.mktime(datetime.datetime.now().timetuple())
        bucket_num = int((now_epoch / (60 * 60 * 24)) % self.PERIOD)

        highest_team_key = Team.query().order(-Team.team_number).fetch(1, keys_only=True)[0]
        highest_team_num = int(highest_team_key.id()[3:])
        bucket_size = int(highest_team_num / (self.PERIOD)) + 1

        min_team = bucket_num * bucket_size
        max_team = min_team + bucket_size
        team_keys = Team.query(Team.team_number >= min_team, Team.team_number < max_team).fetch(1000, keys_only=True)

        teams = ndb.get_multi(team_keys)
        for team in teams:
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_team_details/' + team.key_name,
                method='GET')

        # FIXME omg we're just writing out? -fangeugene 2013 Nov 6
        self.response.out.write("Bucket number {} out of {}<br>".format(bucket_num, self.PERIOD))
        self.response.out.write("{} team gets have been enqueued in the interval [{}, {}).".format(len(teams), min_team, max_team))


class UsfirstTeamDetailsGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST team information page and updating the
    model accordingly.
    """
    def get(self, key_name):
        df = DatafeedUsfirst()
        team = df.getTeamDetails(Team.get_by_id(key_name))
        if not team:
            logging.warning("getTeamDetails with DatafeedUsfirst for event id {} failed. Retrying with DatafeedUsfirstLegacy.".format(key_name))
            legacy_df = DatafeedUsfirstLegacy()
            team = legacy_df.getTeamDetails(Team.get_by_id(key_name))

        if team:
            team = TeamManipulator.createOrUpdate(team)
            success = True
        else:
            success = False

        template_values = {
            'key_name': key_name,
            'team': team,
            'success': success,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_team_details_get.html')
        self.response.out.write(template.render(path, template_values))


class UsfirstPre2003TeamEventsEnqueue(webapp.RequestHandler):
    def get(self):
        """
        Enqueues TeamEventsGet for teams numbers <= 999 (these teams participated
        in events from 2002 and prior, which we can't scrape normally)
        """
        team_keys = Team.query(Team.team_number <= 999).fetch(10000, keys_only=True)
        teams = ndb.get_multi(team_keys)
        for team in teams:
            taskqueue.add(
                queue_name='usfirst',
                url='/tasks/get/usfirst_pre2003_team_events/{}'.format(team.key_name),
                method='GET')

        self.response.out.write("Pre 2003 event gets have been enqueued for %s teams." % (len(teams)))


class UsfirstPre2003TeamEventsGet(webapp.RequestHandler):
    """
    Handles reading a USFIRST team information page and enqueues tasks to
    create events that the team has attended if the event does not exist in the db.
    Also creates appropriate eventteams.
    Doesn't create Championship Event or Championship Divisions
    """
    def get(self, key_name):
        team_key = ndb.Key(Team, key_name)

        df = DatafeedUsfirst()
        first_eids = df.getPre2003TeamEvents(Team.get_by_id(key_name))

        new_eids = []
        for eid in first_eids:
            event_keys = Event.query(Event.first_eid == eid).fetch(10, keys_only=True)
            if len(event_keys) == 0:  # only create events if event not already in db
                try:
                    event = df.getEventDetails(eid)
                except:
                    logging.warning("getEventDetails for eid {} failed.".format(eid))
                    continue

                if event.event_type_enum in {EventType.CMP_DIVISION, EventType.CMP_FINALS}:
                    if event.year >= 2001:
                        # Divisions started in 2001; need to manually create championship events
                        continue
                    else:
                        # No divisions; force event type to be finals
                        event.event_type_enum = EventType.CMP_FINALS

                event = EventManipulator.createOrUpdate(event)
                new_eids.append(eid)
            else:
                event = event_keys[0].get()

            event_team_key_name = event.key.id() + "_" + team_key.id()
            existing_event_team = ndb.Key(EventTeam, event_team_key_name).get()
            if existing_event_team is None:
                event_team = EventTeam(
                    id=event_team_key_name,
                    event=event.key,
                    team=team_key,
                    year=event.year)
                EventTeamManipulator.createOrUpdate(event_team)

        template_values = {'first_eids': first_eids,
                           'new_eids': new_eids}

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/usfirst_team_events_get.html')
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


class OffseasonMatchesGet(webapp.RequestHandler):
    """
    Handles reading an offseason match results page and updating the datastore as needed.
    """
    def get(self, event_key):
        df = DatafeedOffseason()

        event = Event.get_by_id(event_key)
        url = self.request.get('url')

        new_matches = MatchManipulator.createOrUpdate(df.getMatches(event, url))

        template_values = {
            'matches': new_matches,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/offseason_matches_get.html')
        self.response.out.write(template.render(path, template_values))


class TwitterFrcfmsMatchesGet(webapp.RequestHandler):
    """
    Handles getting matches from @FRCFMS on Twitter, and returns a table of
    matches that can be manually manipulated and added
    """
    def get(self):
        df = DatafeedTwitter()

        event_matches = df.getMatches()

        template_values = {
            'event_matches': event_matches,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/datafeeds/twitter_frcfms_matches_get.html')
        self.response.out.write(template.render(path, template_values))
