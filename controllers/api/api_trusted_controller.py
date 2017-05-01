import json
import logging
import webapp2

from google.appengine.ext import ndb

from consts.auth_type import AuthType

from controllers.api.api_base_controller import ApiTrustedBaseController

from datafeeds.parsers.json.json_alliance_selections_parser import JSONAllianceSelectionsParser
from datafeeds.parsers.json.json_awards_parser import JSONAwardsParser
from datafeeds.parsers.json.json_matches_parser import JSONMatchesParser
from datafeeds.parsers.json.json_rankings_parser import JSONRankingsParser
from datafeeds.parsers.json.json_team_list_parser import JSONTeamListParser

from helpers.award_manipulator import AwardManipulator
from helpers.event_manipulator import EventManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.match_helper import MatchHelper
from helpers.match_manipulator import MatchManipulator
from helpers.rankings_helper import RankingsHelper

from models.award import Award
from models.event import Event
from models.event_details import EventDetails
from models.event_team import EventTeam
from models.match import Match
from models.sitevar import Sitevar
from models.team import Team


class ApiTrustedEventAllianceSelectionsUpdate(ApiTrustedBaseController):
    """
    Overwrites an event_detail's alliance_selections with new data
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_ALLIANCES}

    def _process_request(self, request, event_key):
        alliance_selections = JSONAllianceSelectionsParser.parse(request.body)

        event = Event.get_by_id(event_key)

        event_details = EventDetails(
            id=event_key,
            alliance_selections=alliance_selections
        )
        EventDetailsManipulator.createOrUpdate(event_details)

        self.response.out.write(json.dumps({'Success': "Alliance selections successfully updated"}))


class ApiTrustedEventAwardsUpdate(ApiTrustedBaseController):
    """
    Removes all awards for an event and adds the awards given in the request
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_AWARDS}

    def _process_request(self, request, event_key):
        event = Event.get_by_id(event_key)

        awards = []
        for award in JSONAwardsParser.parse(request.body, event_key):
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

        self.response.out.write(json.dumps({'Success': "Awards successfully updated"}))


class ApiTrustedEventMatchesUpdate(ApiTrustedBaseController):
    """
    Creates/updates matches
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_MATCHES}

    def _process_request(self, request, event_key):
        event = Event.get_by_id(event_key)
        year = int(event_key[:4])

        matches = []
        needs_time = []
        for match in JSONMatchesParser.parse(request.body, year):
            match = Match(
                id=Match.renderKeyName(
                    event.key.id(),
                    match.get("comp_level", None),
                    match.get("set_number", 0),
                    match.get("match_number", 0)),
                event=event.key,
                year=event.year,
                set_number=match.get("set_number", 0),
                match_number=match.get("match_number", 0),
                comp_level=match.get("comp_level", None),
                team_key_names=match.get("team_key_names", None),
                alliances_json=match.get("alliances_json", None),
                score_breakdown_json=match.get("score_breakdown_json", None),
                time_string=match.get("time_string", None),
                time=match.get("time", None),
            )

            if (not match.time or match.time == "") and match.time_string:
                # We can calculate the real time from the time string
                needs_time.append(match)
            matches.append(match)

        if needs_time:
            try:
                logging.debug("Calculating time!")
                MatchHelper.add_match_times(event, needs_time)
            except Exception, e:
                logging.error("Failed to calculate match times")

        MatchManipulator.createOrUpdate(matches)

        self.response.out.write(json.dumps({'Success': "Matches successfully updated"}))


class ApiTrustedEventMatchesDelete(ApiTrustedBaseController):
    """
    Deletes given match keys
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_MATCHES}

    def _process_request(self, request, event_key):
        keys_to_delete = set()
        try:
            match_keys = json.loads(request.body)
        except Exception:
            self._errors = json.dumps({"Error": "'keys_to_delete' could not be parsed"})
            self.abort(400)
        for match_key in match_keys:
            keys_to_delete.add(ndb.Key(Match, '{}_{}'.format(event_key, match_key)))

        MatchManipulator.delete_keys(keys_to_delete)

        ret = json.dumps({"keys_deleted": [key.id().split('_')[1] for key in keys_to_delete]})
        self.response.out.write(ret)


class ApiTrustedEventMatchesDeleteAll(ApiTrustedBaseController):
    """
    Deletes all matches
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_MATCHES}

    def _process_request(self, request, event_key):
        if request.body != event_key:
            self._errors = json.dumps({"Error": "To delete all matches for this event, the body of the request must be the event key."})
            self.abort(400)

        keys_to_delete = Match.query(Match.event == ndb.Key(Event, event_key)).fetch(keys_only=True)
        MatchManipulator.delete_keys(keys_to_delete)

        self.response.out.write(json.dumps({'Success': "All matches for {} deleted".format(event_key)}))


class ApiTrustedEventRankingsUpdate(ApiTrustedBaseController):
    """
    Overwrites an event_detail's rankings with new data
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_RANKINGS}

    def _process_request(self, request, event_key):
        rankings = JSONRankingsParser.parse(request.body)

        event_details = EventDetails(
            id=event_key,
            rankings=rankings
        )
        if event_details.year >= 2017:  # TODO: Temporary fix. Should directly parse request into rankings2
            event_details.rankings2 = RankingsHelper.convert_rankings(event_details)
        EventDetailsManipulator.createOrUpdate(event_details)

        self.response.out.write(json.dumps({'Success': "Rankings successfully updated"}))


class ApiTrustedEventTeamListUpdate(ApiTrustedBaseController):
    """
    Creates/updates EventTeams for teams given in the request
    and removes EventTeams for teams not in the request
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_TEAMS}

    def _process_request(self, request, event_key):
        team_keys = JSONTeamListParser.parse(request.body)
        event = Event.get_by_id(event_key)

        event_teams = []
        for team_key in team_keys:
            if Team.get_by_id(team_key):  # Don't create EventTeams for teams that don't exist
                event_teams.append(EventTeam(id=event.key.id() + '_{}'.format(team_key),
                                             event=event.key,
                                             team=ndb.Key(Team, team_key),
                                             year=event.year))

        # delete old eventteams
        old_eventteam_keys = EventTeam.query(EventTeam.event == event.key).fetch(None, keys_only=True)
        to_delete = set(old_eventteam_keys).difference(set([et.key for et in event_teams]))
        EventTeamManipulator.delete_keys(to_delete)

        EventTeamManipulator.createOrUpdate(event_teams)

        self.response.out.write(json.dumps({'Success': "Event teams successfully updated"}))


class ApiTrustedAddMatchYoutubeVideo(ApiTrustedBaseController):
    """
    Adds YouTube videos to matches.
    """
    REQUIRED_AUTH_TYPES = {AuthType.MATCH_VIDEO}

    def _process_request(self, request, event_key):
        try:
            match_videos = json.loads(request.body)
        except Exception:
            self._errors = json.dumps({"Error": "Invalid JSON. Please check input."})
            self.abort(400)

        matches_to_put = []
        for partial_match_key, youtube_id in match_videos.items():
            match_key = '{}_{}'.format(event_key, partial_match_key)
            match = Match.get_by_id(match_key)
            if match is None:
                self._errors = json.dumps({"Error": "Match {} does not exist!".format(match_key)})
                self.abort(400)

            if youtube_id not in match.youtube_videos:
                match.youtube_videos.append(youtube_id)
                matches_to_put.append(match)
        MatchManipulator.createOrUpdate(matches_to_put)

        self.response.out.write(json.dumps({'Success': "Match videos successfully updated"}))
