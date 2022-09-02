from datetime import datetime
import json
import logging
import os

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.event_type import EventType
from consts.playoff_type import PlayoffType
from controllers import event_controller
from controllers.base_controller import LoggedInHandler
from datafeeds.parsers.csv.csv_advancement_parser import CSVAdvancementParser
from datafeeds.parsers.csv.csv_alliance_selections_parser import CSVAllianceSelectionsParser
from datafeeds.parsers.csv.csv_teams_parser import CSVTeamsParser
from helpers.award_manipulator import AwardManipulator
from helpers.event.event_test_creator import EventTestCreator
from helpers.event.event_webcast_adder import EventWebcastAdder
from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.team_manipulator import TeamManipulator
from helpers.location_helper import LocationHelper
from helpers.match_helper import MatchHelper
from helpers.match_manipulator import MatchManipulator
from helpers.memcache.memcache_webcast_flusher import MemcacheWebcastFlusher
from helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from helpers.website_helper import WebsiteHelper
from models.api_auth_access import ApiAuthAccess
from models.district import District
from models.event import Event
from models.event_details import EventDetails
from models.event_team import EventTeam
from models.match import Match
from models.media import Media
from models.sitevar import Sitevar
from models.team import Team
from template_engine import jinja2_engine

import tba_config


class AdminEventAddAllianceSelections(LoggedInHandler):
    """
    Add alliance selections to an Event.
    """
    def post(self, event_key_id):
        self._require_admin()
        event = Event.get_by_id(event_key_id)

        alliance_selections_csv = self.request.get('alliance_selections_csv')
        alliance_selections = CSVAllianceSelectionsParser.parse(alliance_selections_csv)

        event_details = EventDetails(
            id=event_key_id,
            alliance_selections=alliance_selections
        )
        EventDetailsManipulator.createOrUpdate(event_details)

        self.redirect("/admin/event/" + event.key_name)


class AdminAddAllianceBackup(LoggedInHandler):
    """
    Add a backup team into the alliances dict
    """
    def post(self, event_key_id):
        self._require_admin()
        event = Event.get_by_id(event_key_id)
        if not event:
            self.redirect("/admin/event/" + event.key_name)
            return
        event_details = event.details
        if not event_details or not event_details.alliance_selections:
            # No alliance data to modify
            self.redirect("/admin/event/" + event.key_name)
            return

        team_in = "frc{}".format(self.request.get("backup_in"))
        team_out = "frc{}".format(self.request.get("backup_out"))

        # Make sure both teams are attending the event
        et_in = EventTeam.get_by_id("{}_{}".format(event.key_name, team_in))
        et_out = EventTeam.get_by_id("{}_{}".format(event.key_name, team_out))
        if not et_in and et_out:
            # Bad teams supplied
            self.redirect("/admin/event/" + event.key_name)
            return

        for alliance in event_details.alliance_selections:
            if team_out in alliance.get('picks', []):
                alliance['backup'] = {}
                alliance['backup']['in'] = team_in
                alliance['backup']['out'] = team_out
                EventDetailsManipulator.createOrUpdate(event_details)
                break

        self.redirect("/admin/event/" + event.key_name)
        return


class AdminPlayoffAdvancementAddController(LoggedInHandler):
    def post(self):
        self._require_admin()

        event_key = self.request.get("event_key").strip()
        event = Event.get_by_id(event_key)
        if not event:
            self.redirect("/admin/event/" + event.key_name)
            return

        if event.playoff_type != PlayoffType.ROUND_ROBIN_6_TEAM:
            logging.warning("Can't set advancement for non-round robin events")
            self.redirect("/admin/event/" + event.key_name)
            return

        advancement_csv = self.request.get("advancement_csv")
        comp_level = self.request.get("comp_level")
        matches_per_team = int(self.request.get("num_matches"))
        if comp_level not in Match.ELIM_LEVELS:
            logging.warning("Bad comp level: {}".format(comp_level))
            self.redirect("/admin/event/" + event.key_name)
            return
        parsed_advancement = CSVAdvancementParser.parse(advancement_csv, matches_per_team)
        advancement = PlayoffAdvancementHelper.generate_playoff_advancement_from_csv(event, parsed_advancement, comp_level)

        cleaned_matches = MatchHelper.delete_invalid_matches(event.matches, event)
        matches = MatchHelper.organized_matches(cleaned_matches)
        bracket_table = PlayoffAdvancementHelper.generateBracket(matches, event, event.alliance_selections)
        comp_levels = bracket_table.keys()
        for comp_level in comp_levels:
            if comp_level != 'f':
                del bracket_table[comp_level]

        existing_details = EventDetails.get_by_id(event.key_name)
        new_advancement = existing_details.playoff_advancement if existing_details and existing_details.playoff_advancement else {}
        new_advancement.update(advancement)
        event_details = EventDetails(
            id=event.key_name,
            playoff_advancement={
                'advancement': new_advancement,
                'bracket': bracket_table,
            },
        )
        EventDetailsManipulator.createOrUpdate(event_details)

        self.redirect("/admin/event/" + event.key_name)
        return


class AdminPlayoffAdvancementPurgeController(LoggedInHandler):
    def post(self, event_key):
        self._require_admin()

        event = Event.get_by_id(event_key)
        if not event:
            self.redirect("/admin/event/" + event.key_name)
            return

        details = EventDetails.get_by_id(event.key_name)
        if details:
            details.playoff_advancement = {}
            EventDetailsManipulator.createOrUpdate(details)

        self.redirect("/admin/event/" + event.key_name)
        return


class AdminEventAddTeams(LoggedInHandler):
    """
    Add a teams to an Event. Useful for legacy and offseason events.
    """
    def post(self, event_key_id):
        self._require_admin()
        event = Event.get_by_id(event_key_id)

        teams_csv = self.request.get('teams_csv')
        team_numbers = CSVTeamsParser.parse(teams_csv)

        event_teams = []
        teams = []
        for team_number in team_numbers:
            event_teams.append(EventTeam(id=event.key.id() + '_frc{}'.format(team_number),
                                         event=event.key,
                                         team=ndb.Key(Team, 'frc{}'.format(team_number)),
                                         year=event.year))
            teams.append(Team(id='frc{}'.format(team_number),
                              team_number=int(team_number)))

        EventTeamManipulator.createOrUpdate(event_teams)
        TeamManipulator.createOrUpdate(teams)

        self.redirect("/admin/event/" + event.key_name)


class AdminEventDeleteTeams(LoggedInHandler):
    """
    Remove teams from an Event. Useful for legacy and offseason events.
    """
    def post(self, event_key_id):
        self._require_admin()
        event = Event.get_by_id(event_key_id)

        teams_csv = self.request.get('teams_csv')
        team_numbers = CSVTeamsParser.parse(teams_csv)

        event_teams = []
        for team_number in team_numbers:
            event_teams.append(ndb.Key(EventTeam, '{}_frc{}'.format(event.key.id(), team_number)))

        EventTeamManipulator.delete_keys(event_teams)

        self.redirect("/admin/event/" + event.key_name)


class AdminEventRemapTeams(LoggedInHandler):
    """
    Remaps teams within an Event. Useful for offseason events.
    eg: 9254 -> 254B
    """
    def post(self, event_key_id):
        self._require_admin()
        event = Event.get_by_id(event_key_id)

        remap_teams = {}
        for key, value in json.loads(self.request.get('remap_teams')).items():
            remap_teams['frc{}'.format(key)] = 'frc{}'.format(value)

        event.remap_teams = remap_teams
        EventManipulator.createOrUpdate(event)

        taskqueue.add(
            url='/tasks/do/remap_teams/{}'.format(event.key_name),
            method='GET',
            queue_name='admin',
        )

        self.redirect("/admin/event/" + event.key_name)


class AdminEventAddWebcast(LoggedInHandler):
    """
    Add a webcast to an Event.
    """
    def post(self, event_key_id):
        self._require_admin()

        webcast = dict()
        webcast["type"] = self.request.get("webcast_type")
        webcast["channel"] = self.request.get("webcast_channel")
        if self.request.get("webcast_file"):
            webcast["file"] = self.request.get("webcast_file")

        event = Event.get_by_id(event_key_id)
        EventWebcastAdder.add_webcast(event, webcast)

        self.redirect("/admin/event/" + event.key_name)


class AdminEventRemoveWebcast(LoggedInHandler):
    """
    Remove a webcast from an event
    """
    def post(self, event_key_id):
        self._require_admin()

        event = Event.get_by_id(event_key_id)
        if not event:
            self.abort(404)

        type = self.request.get("type")
        channel = self.request.get("channel")
        index = int(self.request.get("index")) - 1
        if self.request.get("file"):
            file = self.request.get("file")
        else:
            file = None
        EventWebcastAdder.remove_webcast(event, index, type, channel, file)
        self.redirect("/admin/event/{}#webcasts".format(event.key_name))


class AdminRefetchEventLocation(LoggedInHandler):
    """
    Force geocoding an event's location
    """
    def get(self, event_key_id):
        self._require_admin()

        event = Event.get_by_id(event_key_id)
        if not event:
            self.abort(404)

        event.normalized_location = None
        LocationHelper.update_event_location(event)
        event = EventManipulator.createOrUpdate(event)

        self.response.out.write("New location: {}".format(event.normalized_location))

    def post(self, event_key_id):
        self._require_admin()

        event = Event.get_by_id(event_key_id)
        if not event:
            self.abort(404)

        place_id = self.request.get('place_id')
        if not place_id:
            self.abort(400)

        # Construct a mostly empty input struct that'll get filled in
        location_input = {
            'place_id': place_id,
            'geometry': {
                'location': {
                    'lat': '',
                    'lng': '',
                },
            },
            'name': '',
            'types': [],
        }

        location_info = LocationHelper.construct_location_info_async(location_input).get_result()
        event.normalized_location = LocationHelper.build_normalized_location(location_info)
        EventManipulator.createOrUpdate(event)
        self.redirect('/admin/event/{}'.format(event_key_id))


class AdminEventCreateTest(LoggedInHandler):
    """
    Create a test event that is happening now.
    """
    def get(self):
        self._require_admin()

        if tba_config.CONFIG["env"] != "prod":
            EventTestCreator.createPastEvent()
            EventTestCreator.createFutureEvent()
            EventTestCreator.createPresentEvent()
            self.redirect("/events/")
        else:
            logging.error("{} tried to create test events in prod! No can do.".format(
                self.user_bundle.user.email()))
            self.redirect("/admin/")


class AdminEventDeleteMatches(LoggedInHandler):
    """
    Remove a comp level's matches
    """
    def get(self, event_key, comp_level, to_delete):
        self._require_admin()

        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)

        organized_matches = MatchHelper.organized_matches(event.matches)
        if comp_level not in organized_matches:
            self.abort(400)
            return

        matches_to_delete = []
        if to_delete == 'all':
            matches_to_delete = [m for m in organized_matches[comp_level]]
        elif to_delete == 'unplayed':
            matches_to_delete = [m for m in organized_matches[comp_level] if not m.has_been_played]

        delete_count = len(matches_to_delete)
        if matches_to_delete:
            MatchManipulator.delete(matches_to_delete)

        self.redirect("/admin/event/{}?deleted={}#matches".format(event_key, delete_count))
