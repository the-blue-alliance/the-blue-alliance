from datetime import datetime
import json
import logging
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.event_type import EventType
from consts.playoff_type import PlayoffType
from controllers import event_controller
from controllers.base_controller import LoggedInHandler
from datafeeds.csv_alliance_selections_parser import CSVAllianceSelectionsParser
from datafeeds.csv_teams_parser import CSVTeamsParser
from helpers.award_manipulator import AwardManipulator
from helpers.event.event_test_creator import EventTestCreator
from helpers.event.event_webcast_adder import EventWebcastAdder
from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.team_manipulator import TeamManipulator
from helpers.match_manipulator import MatchManipulator
from helpers.memcache.memcache_webcast_flusher import MemcacheWebcastFlusher
from helpers.website_helper import WebsiteHelper
from models.api_auth_access import ApiAuthAccess
from models.district import District
from models.event import Event
from models.event_details import EventDetails
from models.event_team import EventTeam
from models.match import Match
from models.media import Media
from models.team import Team

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
        event.prepAwardsMatchesTeams()

        remap_teams = {}
        for key, value in json.loads(self.request.get('remap_teams')).items():
            remap_teams['frc{}'.format(key)] = 'frc{}'.format(value)

        # Remap matches
        EventHelper.remapteams_matches(event.matches, remap_teams)
        MatchManipulator.createOrUpdate(event.matches)

        # Remap alliance selections
        if event.alliance_selections:
            EventHelper.remapteams_alliances(event.alliance_selections, remap_teams)
        # Remap rankings
        if event.rankings:
            EventHelper.remapteams_rankings(event.rankings, remap_teams)
        if event.details and event.details.rankings2:
            EventHelper.remapteams_rankings2(event.details.rankings2, remap_teams)
        EventDetailsManipulator.createOrUpdate(event.details)

        # Remap awards
        EventHelper.remapteams_awards(event.awards, remap_teams)
        AwardManipulator.createOrUpdate(event.awards, auto_union=False)

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


class AdminEventCreate(LoggedInHandler):
    """
    Create an Event. POSTs to AdminEventEdit.
    """
    def get(self):
        self._require_admin()

        self.template_values.update({
            "event_types": EventType.type_names,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_create.html')
        self.response.out.write(template.render(path, self.template_values))


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


class AdminEventDelete(LoggedInHandler):
    """
    Delete an Event.
    """
    def get(self, event_key_id):
        self._require_admin()

        event = Event.get_by_id(event_key_id)

        self.template_values.update({
            "event": event
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_delete.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, event_key_id):
        self._require_admin()

        logging.warning("Deleting %s at the request of %s / %s" % (
            event_key_id,
            self.user_bundle.user.user_id(),
            self.user_bundle.user.email()))

        event = Event.get_by_id(event_key_id)

        matches = Match.query(Match.event == event.key).fetch(5000)
        MatchManipulator.delete(matches)

        event_teams = EventTeam.query(EventTeam.event == event.key).fetch(5000)
        EventTeamManipulator.delete(event_teams)

        EventManipulator.delete(event)

        self.redirect("/admin/events?deleted=%s" % event_key_id)


class AdminEventDetail(LoggedInHandler):
    """
    Show an Event.
    """
    def get(self, event_key):
        self._require_admin()

        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)
        event.prepAwardsMatchesTeams()

        api_keys = ApiAuthAccess.query(ApiAuthAccess.event_list == ndb.Key(Event, event_key)).fetch()
        event_medias = Media.query(Media.references == event.key).fetch(500)

        self.template_values.update({
            "event": event,
            "medias": event_medias,
            "cache_key": event_controller.EventDetail('2016nyny').cache_key.format(event.key_name),
            "flushed": self.request.get("flushed"),
            "playoff_types": PlayoffType.type_names,
            "write_auths": api_keys,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_details.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminEventEdit(LoggedInHandler):
    """
    Edit an Event.
    """
    def get(self, event_key):
        self._require_admin()

        event = Event.get_by_id(event_key)

        self.template_values.update({
            "event": event,
            'alliance_selections': json.dumps(event.alliance_selections),
            'rankings': json.dumps(event.rankings),
            "playoff_types": PlayoffType.type_names,
            "event_types": EventType.type_names,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, event_key):
        self._require_admin()

        # Note, we don't actually use event_key.

        start_date = None
        if self.request.get("start_date"):
            start_date = datetime.strptime(self.request.get("start_date"), "%Y-%m-%d")

        end_date = None
        if self.request.get("end_date"):
            end_date = datetime.strptime(self.request.get("end_date"), "%Y-%m-%d")

        first_code = self.request.get("first_code", None)
        district_key = self.request.get("event_district_key", None)
        parent_key = self.request.get("parent_event", None)

        division_key_names = json.loads(self.request.get('divisions'), '[]') if self.request.get('divisions') else []
        division_keys = [ndb.Key(Event, key) for key in division_key_names] if division_key_names else []

        website = WebsiteHelper.format_url(self.request.get("website"))

        event = Event(
            id=str(self.request.get("year")) + str.lower(str(self.request.get("event_short"))),
            end_date=end_date,
            event_short=self.request.get("event_short"),
            first_code=first_code if first_code and first_code != 'None' else None,
            event_type_enum=int(self.request.get("event_type")) if self.request.get('event_type') else EventType.UNLABLED,
            district_key=ndb.Key(District, self.request.get("event_district_key")) if district_key and district_key != 'None' else None,
            venue=self.request.get("venue"),
            venue_address=self.request.get("venue_address"),
            city=self.request.get("city"),
            state_prov=self.request.get("state_prov"),
            postalcode=self.request.get("postalcode"),
            country=self.request.get("country"),
            name=self.request.get("name"),
            short_name=self.request.get("short_name"),
            start_date=start_date,
            website=website,
            year=int(self.request.get("year")),
            official={"true": True, "false": False}.get(self.request.get("official").lower()),
            enable_predictions={"true": True, "false": False}.get(self.request.get("enable_predictions").lower()),
            facebook_eid=self.request.get("facebook_eid"),
            custom_hashtag=self.request.get("custom_hashtag"),
            webcast_json=self.request.get("webcast_json"),
            playoff_type=int(self.request.get("playoff_type")) if self.request.get('playoff_type') else PlayoffType.BRACKET_8_TEAM,
            parent_event=ndb.Key(Event, parent_key) if parent_key and parent_key.lower() != 'none' else None,
            divisions=division_keys,
        )
        event = EventManipulator.createOrUpdate(event)

        if self.request.get("alliance_selections_json") or self.request.get("rankings_json"):
            event_details = EventDetails(
                id=event_key,
                alliance_selections=json.loads(self.request.get("alliance_selections_json")),
                rankings=json.loads(self.request.get("rankings_json"))
            )
            EventDetailsManipulator.createOrUpdate(event_details)

        MemcacheWebcastFlusher.flushEvent(event.key_name)

        self.redirect("/admin/event/" + event.key_name)


class AdminEventList(LoggedInHandler):
    """
    List all Events.
    """
    VALID_YEARS = range(1992, tba_config.MAX_YEAR + 1)

    def get(self, year=None):
        self._require_admin()

        if year is not None:
            year = int(year)
        else:
            year = datetime.now().year

        events = Event.query(Event.year == year).order(Event.start_date).fetch(10000)

        self.template_values.update({
            "valid_years": self.VALID_YEARS,
            "selected_year": year,
            "events": events,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_list.html')
        self.response.out.write(template.render(path, self.template_values))
