import json
import logging
import re
import webapp2

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from consts.auth_type import AuthType
from consts.media_type import MediaType
from controllers.api.api_base_controller import ApiTrustedBaseController

from datafeeds.parser_base import ParserInputException
from datafeeds.parsers.json.json_alliance_selections_parser import JSONAllianceSelectionsParser
from datafeeds.parsers.json.json_awards_parser import JSONAwardsParser
from datafeeds.parsers.json.json_matches_parser import JSONMatchesParser
from datafeeds.parsers.json.json_rankings_parser import JSONRankingsParser
from datafeeds.parsers.json.json_team_list_parser import JSONTeamListParser
from datafeeds.parsers.json.json_zebra_motionworks_parser import JSONZebraMotionWorksParser

from helpers.award_manipulator import AwardManipulator
from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.event.event_webcast_adder import EventWebcastAdder
from helpers.match_helper import MatchHelper
from helpers.match_manipulator import MatchManipulator
from helpers.media_manipulator import MediaManipulator
from helpers.memcache.memcache_webcast_flusher import MemcacheWebcastFlusher
from helpers.rankings_helper import RankingsHelper
from helpers.webcast_helper import WebcastParser

from models.award import Award
from models.event import Event
from models.event_details import EventDetails
from models.event_team import EventTeam
from models.match import Match
from models.media import Media
from models.team import Team
from models.zebra_motionworks import ZebraMotionWorks


class ApiTrustedEventAllianceSelectionsUpdate(ApiTrustedBaseController):
    """
    Overwrites an event_detail's alliance_selections with new data
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_ALLIANCES}

    def _process_request(self, request, event_key):
        alliance_selections = JSONAllianceSelectionsParser.parse(request.body)

        event_details = EventDetails(
            id=event_key,
            alliance_selections=alliance_selections
        )

        if self.event.remap_teams:
            EventHelper.remapteams_alliances(event_details.alliance_selections, self.event.remap_teams)
        EventDetailsManipulator.createOrUpdate(event_details)

        self.response.out.write(json.dumps({'Success': "Alliance selections successfully updated"}))


class ApiTrustedEventAwardsUpdate(ApiTrustedBaseController):
    """
    Removes all awards for an event and adds the awards given in the request
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_AWARDS}

    def _process_request(self, request, event_key):
        awards = []
        for award in JSONAwardsParser.parse(request.body, event_key):
            awards.append(Award(
                id=Award.render_key_name(self.event.key_name, award['award_type_enum']),
                name_str=award['name_str'],
                award_type_enum=award['award_type_enum'],
                year=self.event.year,
                event=self.event.key,
                event_type_enum=self.event.event_type_enum,
                team_list=[ndb.Key(Team, team_key) for team_key in award['team_key_list']],
                recipient_json_list=award['recipient_json_list']
            ))

        # it's easier to clear all awards and add new ones than try to find the difference
        old_award_keys = Award.query(Award.event == self.event.key).fetch(None, keys_only=True)
        AwardManipulator.delete_keys(old_award_keys)

        if self.event.remap_teams:
            EventHelper.remapteams_awards(awards, self.event.remap_teams)
        AwardManipulator.createOrUpdate(awards)

        self.response.out.write(json.dumps({'Success': "Awards successfully updated"}))


class ApiTrustedEventMatchesUpdate(ApiTrustedBaseController):
    """
    Creates/updates matches
    """
    REQUIRED_AUTH_TYPES = {AuthType.EVENT_MATCHES}

    def _process_request(self, request, event_key):
        matches = []
        needs_time = []
        for match in JSONMatchesParser.parse(request.body, self.event.year):
            match = Match(
                id=Match.renderKeyName(
                    self.event.key.id(),
                    match.get("comp_level", None),
                    match.get("set_number", 0),
                    match.get("match_number", 0)),
                event=self.event.key,
                year=self.event.year,
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
                MatchHelper.add_match_times(self.event, needs_time)
            except Exception, e:
                logging.error("Failed to calculate match times")

        if self.event.remap_teams:
            EventHelper.remapteams_matches(matches, self.event.remap_teams)
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

        if self.event.remap_teams:
            EventHelper.remapteams_rankings(event_details.rankings, self.event.remap_teams)
            # TODO: Remap rankings2 directly

        if event_details.year >= 2018:  # TODO: Temporary fix. Should directly parse request into rankings2
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

        event_teams = []
        for team_key in team_keys:
            if Team.get_by_id(team_key):  # Don't create EventTeams for teams that don't exist
                event_teams.append(EventTeam(id=self.event.key.id() + '_{}'.format(team_key),
                                             event=self.event.key,
                                             team=ndb.Key(Team, team_key),
                                             year=self.event.year))

        # delete old eventteams
        old_eventteam_keys = EventTeam.query(EventTeam.event == self.event.key).fetch(None, keys_only=True)
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


class ApiTrustedAddEventMedia(ApiTrustedBaseController):
    """
    Add media linked to an event
    """

    REQUIRED_AUTH_TYPES = {AuthType.MATCH_VIDEO}

    def _process_request(self, request, event_key):
        try:
            video_list = json.loads(request.body)
        except Exception:
            self._errors = json.dumps({"Error": "Invalid JSON. Please check input."})
            self.abort(400)
            return

        if not isinstance(video_list, list) or not video_list:
            self._errors = json.dumps({"Error": "Invalid JSON. Please check input."})
            self.abort(400)
            return

        media_to_put = []
        event_reference = Media.create_reference('event', self.event.key_name)
        for youtube_id in video_list:
            media = Media(
                id=Media.render_key_name(MediaType.YOUTUBE_VIDEO, youtube_id),
                foreign_key=youtube_id,
                media_type_enum=MediaType.YOUTUBE_VIDEO,
                details_json=None,
                private_details_json=None,
                year=self.event.year,
                references=[event_reference],
                preferred_references=[],
            )
            media_to_put.append(media)

        MediaManipulator.createOrUpdate(media_to_put)


class ApiTrustedUpdateEventInfo(ApiTrustedBaseController):
    """
    Allow configuring fields for an event
    """

    REQUIRED_AUTH_TYPES = {AuthType.EVENT_INFO}

    ALLOWED_EVENT_PARAMS = {
        "first_event_code",
        "playoff_type",
        "webcasts",  # this is a list of stream URLs, we'll mutate it ourselves
        "remap_teams",
    }

    def _process_request(self, request, event_key):
        try:
            event_info = json.loads(request.body)
        except Exception:
            self._errors = json.dumps({"Error": "Invalid json. Check input."})
            self.abort(400)

        if not isinstance(event_info, dict) or not event_info:
            self._errors = json.dumps({"Error": "Invalid json. Check input."})
            self.abort(400)

        do_team_remap = False
        for field, value in event_info.iteritems():
            if field not in self.ALLOWED_EVENT_PARAMS:
                continue

            if field == "webcasts":
                # Do special processing here because webcasts are janky
                if not isinstance(value, list):
                    self._errors = json.dumps(
                        {"Error": "Invalid json. Check input"}
                    )
                    self.abort(400)
                    return
                webcast_list = []
                for webcast in value:
                    if not isinstance(webcast, dict):
                        self._errors = json.dumps(
                            {"Error": "Invalid json. Check input"}
                        )
                        self.abort(400)
                        return
                    if 'url' in webcast:
                        webcast_list.append(
                            WebcastParser.webcast_dict_from_url(webcast['url'])
                        )
                    elif 'type' in webcast and 'channel' in webcast:
                        webcast_list.append(webcast)

                webcast_list = [w for w in webcast_list if w is not None]
                EventWebcastAdder.add_webcast(
                    self.event,
                    webcast_list,
                    False,  # Don't createOrUpdate yet
                )
            elif field == "remap_teams":
                # Validate remap_teams
                if not isinstance(value, dict):
                    raise ParserInputException("Invalid reamap_teams. Check input")
                for temp_team, remapped_team in value.items():
                    temp_match = re.match(r'frc\d+', str(temp_team))
                    remapped_match = re.match(r'frc\d+[B-Z]?', str(remapped_team))
                    if not temp_match or (temp_match and (temp_match.group(0) != str(temp_team))):
                        raise ParserInputException("Bad team: '{}'. Must follow format 'frcXXX'.".format(temp_team))
                    if not remapped_match or (remapped_match and (remapped_match.group(0) != str(remapped_team))):
                        raise ParserInputException("Bad team: '{}'. Must follow format 'frcXXX' or 'frcXXX[B-Z]'.".format(remapped_team))
                do_team_remap = True
                setattr(self.event, field, value)
            else:
                try:
                    if field == "first_event_code":
                        self.event.official = value is not None
                        field = "first_code"  # Internal property is different
                    setattr(self.event, field, value)
                except Exception, e:
                    self._errors({
                        "Error": "Unable to set event field",
                        "Message": str(e)
                    })
                    self.abort(400)

        EventManipulator.createOrUpdate(self.event)
        if "webcast" in event_info:
            MemcacheWebcastFlusher.flushEvent(self.event.key_name)

        if do_team_remap:
            taskqueue.add(
                url='/tasks/do/remap_teams/{}'.format(self.event.key_name),
                method='GET',
                queue_name='admin',
            )


class ApiTrustedAddMatchZebraMotionWorks(ApiTrustedBaseController):
    """
    Add Zebra MotionWorks data linked to a match
    """

    REQUIRED_AUTH_TYPES = {AuthType.ZEBRA_MOTIONWORKS}

    def _process_request(self, request, event_key):
        to_put = []
        for zebra_data in JSONZebraMotionWorksParser.parse(request.body):
            match_key = zebra_data['key']

            # Check that match_key matches event_key
            if match_key.split('_')[0] != event_key:
                self._errors = json.dumps({"Error": "Match key {} does not match Event key {}!".format(match_key, event_key)})
                self.abort(400)

            # Check that match exists
            match = Match.get_by_id(match_key)
            if match is None:
                self._errors = json.dumps({"Error": "Match {} does not exist!".format(match_key)})
                self.abort(400)

            # Check that teams in Zebra data and teams in Match are the same
            for color in ['red', 'blue']:
                match_teams = match.alliances[color]['teams']
                zebra_teams = [team['team_key'] for team in zebra_data['alliances'][color]]
                if match_teams != zebra_teams:
                    self._errors = json.dumps({"Error": "Match {} teams are not valid!".format(match_key)})
                    self.abort(400)

            to_put.append(ZebraMotionWorks(id=match_key, event=ndb.Key(Event, event_key), data=zebra_data))
        ndb.put_multi(to_put)
