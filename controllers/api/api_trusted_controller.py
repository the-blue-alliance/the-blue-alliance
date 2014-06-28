import json
import logging
import webapp2

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from controllers.api.api_base_controller import ApiTrustedBaseController

from datafeeds.parsers.json.json_alliance_selections_parser import JSONAllianceSelectionsParser
from datafeeds.parsers.json.json_awards_parser import JSONAwardsParser
from datafeeds.parsers.json.json_matches_parser import JSONMatchesParser
from datafeeds.parsers.json.json_rankings_parser import JSONRankingsParser
from datafeeds.parsers.json.json_team_list_parser import JSONTeamListParser

from helpers.award_manipulator import AwardManipulator
from helpers.event_manipulator import EventManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.match_manipulator import MatchManipulator

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.sitevar import Sitevar
from models.team import Team


class ApiTrustedEventAllianceSelectionsUpdate(ApiTrustedBaseController):
    def _process_request(self, request, event_key):
        alliances_json = request.get('alliances')
        if not alliances_json:
            self._errors = json.dumps({"Error": "Must provide a request parameter 'alliances'"})
            self.abort(400)

        alliance_selections = JSONAllianceSelectionsParser.parse(alliances_json)

        event = Event.get_by_id(event_key)
        event.alliance_selections_json = json.dumps(alliance_selections)
        event.dirty = True  # TODO: hacky
        EventManipulator.createOrUpdate(event)


class ApiTrustedEventAwardsUpdate(ApiTrustedBaseController):
    def _process_request(self, request, event_key):
        awards_json = request.get('awards')
        if not awards_json:
            self._errors = json.dumps({"Error": "Must provide a request parameter 'awards'"})
            self.abort(400)

        event = Event.get_by_id(event_key)

        awards = []
        for award in JSONAwardsParser.parse(awards_json, event_key):
            awards.append(Award(
                id=Award.render_key_name(event.key_name, award['award_type_enum']),
                name_str=award['name_str'],
                award_type_enum=award['award_type_enum'],
                year=event.year,
                event=event.key,
                event_type_enum=event.event_type_enum,
                team_list=[ndb.Key(Team, team_key) for team_key in award['team_key_list']],
                recipient_json_list=award['recipient_json_list']
            ))

        # it's easier to clear all awards and add new ones than try to find the difference
        old_award_keys = Award.query(Award.event == event.key).fetch(None, keys_only=True)
        AwardManipulator.delete_keys(old_award_keys)

        AwardManipulator.createOrUpdate(awards)


class ApiTrustedEventMatchesUpdate(ApiTrustedBaseController):
    def _process_request(self, request, event_key):
        matches_json = request.get('matches')
        if not matches_json:
            self._errors = json.dumps({"Error": "Must provide a request parameter 'matches'"})
            self.abort(400)

        match_keys_to_delete = request.get('keys_to_delete')
        keys_to_delete = set()
        if match_keys_to_delete:
            try:
                match_keys = json.loads(match_keys_to_delete)
            except Exception:
                self._errors = json.dumps({"Error": "'keys_to_delete' could not be parsed"})
                self.abort(400)
            for match_key in match_keys:
                if match_key.split('_')[0] == event_key:  # Very important! Don't delete matches from events that aren't authorized.
                    keys_to_delete.add(ndb.Key(Match, match_key))

        event = Event.get_by_id(event_key)

        matches = [Match(
            id=Match.renderKeyName(
                event.key.id(),
                match.get("comp_level", None),
                match.get("set_number", 0),
                match.get("match_number", 0)),
            event=event.key,
            game=Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
            set_number=match.get("set_number", 0),
            match_number=match.get("match_number", 0),
            comp_level=match.get("comp_level", None),
            team_key_names=match.get("team_key_names", None),
            alliances_json=match.get("alliances_json", None),
            time_string=match.get("time_string", None),
        ) for match in JSONMatchesParser.parse(matches_json)]

        MatchManipulator.delete_keys(keys_to_delete)
        MatchManipulator.createOrUpdate(matches)
        taskqueue.add(url='/tasks/math/do/event_matchstats/{}'.format(event_key), method='GET')

        self.response.out.write(json.dumps({'keys_deleted': [key.id() for key in keys_to_delete]}))


class ApiTrustedEventRankingsUpdate(ApiTrustedBaseController):
    def _process_request(self, request, event_key):
        rankings_json = request.get('rankings')
        if not rankings_json:
            self._errors = json.dumps({"Error": "Must provide a request parameter 'rankings'"})
            self.abort(400)

        rankings = JSONRankingsParser.parse(rankings_json)

        event = Event.get_by_id(event_key)
        event.rankings_json = json.dumps(rankings)
        event.dirty = True  # TODO: hacky
        EventManipulator.createOrUpdate(event)


class ApiTrustedEventTeamListUpdate(ApiTrustedBaseController):
    def _process_request(self, request, event_key):
        team_list_json = request.get('team_list')
        if not team_list_json:
            self._errors = json.dumps({"Error": "Must provide a request parameter 'team_list'"})
            self.abort(400)

        team_keys = JSONTeamListParser.parse(team_list_json)
        event = Event.get_by_id(event_key)

        event_teams = []
        for team_key in team_keys:
            event_teams.append(EventTeam(id=event.key.id() + '_{}'.format(team_key),
                                         event=event.key,
                                         team=ndb.Key(Team, team_key),
                                         year=event.year))

        # delete old eventteams
        old_eventteam_keys = EventTeam.query(EventTeam.event == event.key).fetch(None, keys_only=True)
        to_delete = set(old_eventteam_keys).difference(set([et.key for et in event_teams]))
        EventTeamManipulator.delete_keys(to_delete)

        EventTeamManipulator.createOrUpdate(event_teams)


class ApiTrustedAddMatchYoutubeVideo(webapp2.RequestHandler):
    def post(self):
        trusted_api_secret = Sitevar.get_by_id("trusted_api.secret")
        if trusted_api_secret is None:
            raise Exception("Missing sitevar: trusted_api.secret. Can't accept YouTube Videos.")

        secret = self.request.get('secret', None)
        if secret is None:
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "No secret given"}))
            return

        if str(trusted_api_secret.values_json) != str(secret):
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "Incorrect secret"}))
            return

        match_key = self.request.get('match_key', None)
        if match_key is None:
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "No match_key given"}))
            return

        youtube_id = self.request.get('youtube_id', None)
        if youtube_id is None:
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "No youtube_id given"}))
            return

        match = Match.get_by_id(match_key)
        if match is None:
            self.response.set_status(400)
            self.response.out.write(json.dumps({"400": "Match {} does not exist!".format(match_key)}))
            return

        if youtube_id not in match.youtube_videos:
            match.youtube_videos.append(youtube_id)
            match.dirty = True  # This is so hacky. -fangeugene 2014-03-06
            MatchManipulator.createOrUpdate(match)
