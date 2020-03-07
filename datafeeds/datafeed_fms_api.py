import base64
import cloudstorage
import datetime
import json
import logging
import tba_config
import traceback

from google.appengine.ext import ndb

from consts.event_type import EventType
from controllers.api.api_status_controller import ApiStatusController
from datafeeds.datafeed_base import DatafeedBase
from models.district import District
from models.event import Event
from models.event_team import EventTeam
from models.sitevar import Sitevar

from parsers.fms_api.fms_api_awards_parser import FMSAPIAwardsParser
from parsers.fms_api.fms_api_district_list_parser import FMSAPIDistrictListParser
from parsers.fms_api.fms_api_district_rankings_parser import FMSAPIDistrictRankingsParser
from parsers.fms_api.fms_api_event_alliances_parser import FMSAPIEventAlliancesParser
from parsers.fms_api.fms_api_event_list_parser import FMSAPIEventListParser
from parsers.fms_api.fms_api_event_rankings_parser import FMSAPIEventRankingsParser, FMSAPIEventRankings2Parser
from parsers.fms_api.fms_api_match_parser import FMSAPIHybridScheduleParser, FMSAPIMatchDetailsParser
from parsers.fms_api.fms_api_team_details_parser import FMSAPITeamDetailsParser
from parsers.fms_api.fms_api_team_avatar_parser import FMSAPITeamAvatarParser


class DatafeedFMSAPI(object):
    EVENT_SHORT_EXCEPTIONS = {
        'arc': 'archimedes',
        'cars': 'carson',
        'carv': 'carver',
        'cur': 'curie',
        'dal': 'daly',
        'dar': 'darwin',
        'gal': 'galileo',
        'hop': 'hopper',
        'new': 'newton',
        'roe': 'roebling',
        'tes': 'tesla',
        'tur': 'turing',
    }

    SUBDIV_TO_DIV = {  # 2015, 2016
        'arc': 'arte',
        'cars': 'gaca',
        'carv': 'cuca',
        'cur': 'cuca',
        'gal': 'gaca',
        'hop': 'neho',
        'new': 'neho',
        'tes': 'arte',
    }

    SUBDIV_TO_DIV_2017 = {  # 2017+
        'arc': 'arda',
        'cars': 'cate',
        'carv': 'cane',
        'cur': 'cuda',
        'dal': 'arda',
        'dar': 'cuda',
        'gal': 'garo',
        'hop': 'hotu',
        'new': 'cane',
        'roe': 'garo',
        'tes': 'cate',
        'tur': 'hotu',
    }

    SAVED_RESPONSE_DIR_PATTERN = '/tbatv-prod-hrd.appspot.com/frc-api-response/{}/'  # % (url)

    def __init__(self, version, sim_time=None, save_response=False):
        self._sim_time = sim_time
        self._save_response = save_response and sim_time is None
        fms_api_secrets = Sitevar.get_by_id('fmsapi.secrets')
        if fms_api_secrets is None:
            if self._sim_time is None:
                raise Exception("Missing sitevar: fmsapi.secrets. Can't access FMS API.")
        else:
            fms_api_username = fms_api_secrets.contents['username']
            fms_api_authkey = fms_api_secrets.contents['authkey']
            self._fms_api_authtoken = base64.b64encode('{}:{}'.format(fms_api_username, fms_api_authkey))

        self._is_down_sitevar = Sitevar.get_by_id('apistatus.fmsapi_down')
        if not self._is_down_sitevar:
            self._is_down_sitevar = Sitevar(id="apistatus.fmsapi_down", description="Is FMSAPI down?")

        self.FMS_API_DOMAIN = 'https://frc-api.firstinspires.org/'
        if version == 'v1.0':
            FMS_API_URL_BASE = self.FMS_API_DOMAIN + 'api/v1.0'
            self.FMS_API_AWARDS_URL_PATTERN = FMS_API_URL_BASE + '/awards/%s/%s'  # (year, event_short)
            self.FMS_API_HYBRID_SCHEDULE_QUAL_URL_PATTERN = FMS_API_URL_BASE + '/schedule/%s/%s/qual/hybrid'  # (year, event_short)
            self.FMS_API_HYBRID_SCHEDULE_PLAYOFF_URL_PATTERN = FMS_API_URL_BASE + '/schedule/%s/%s/playoff/hybrid'  # (year, event_short)
            self.FMS_API_EVENT_RANKINGS_URL_PATTERN = FMS_API_URL_BASE + '/rankings/%s/%s'  # (year, event_short)
            self.FMS_API_EVENT_ALLIANCES_URL_PATTERN = FMS_API_URL_BASE + '/alliances/%s/%s'  # (year, event_short)
            self.FMS_API_TEAM_DETAILS_URL_PATTERN = FMS_API_URL_BASE + '/teams/%s/?teamNumber=%s'  # (year, teamNumber)
            self.FMS_API_TEAM_AVATAR_URL_PATTERN = FMS_API_URL_BASE + '/%s/avatars/?teamNumber=%s'  # (year, teamNumber)
            self.FMS_API_EVENT_AVATAR_URL_PATTERN = FMS_API_URL_BASE + '/%s/avatars/?eventCode=%s&page=%s'  # (year, eventCode, page)
            self.FMS_API_EVENT_LIST_URL_PATTERN = FMS_API_URL_BASE + '/events/season=%s'
            self.FMS_API_EVENTTEAM_LIST_URL_PATTERN = FMS_API_URL_BASE + '/teams/?season=%s&eventCode=%s&page=%s'  # (year, eventCode, page)
        elif version == 'v2.0':
            FMS_API_URL_BASE = self.FMS_API_DOMAIN + 'v2.0'
            self.FMS_API_AWARDS_URL_PATTERN = FMS_API_URL_BASE + '/%s/awards/%s'  # (year, event_short)
            self.FMS_API_HYBRID_SCHEDULE_QUAL_URL_PATTERN = FMS_API_URL_BASE + '/%s/schedule/%s/qual/hybrid'  # (year, event_short)
            self.FMS_API_HYBRID_SCHEDULE_PLAYOFF_URL_PATTERN = FMS_API_URL_BASE + '/%s/schedule/%s/playoff/hybrid'  # (year, event_short)
            self.FMS_API_MATCH_DETAILS_QUAL_URL_PATTERN = FMS_API_URL_BASE + '/%s/scores/%s/qual'  # (year, event_short)
            self.FMS_API_MATCH_DETAILS_PLAYOFF_URL_PATTERN = FMS_API_URL_BASE + '/%s/scores/%s/playoff'  # (year, event_short)
            self.FMS_API_EVENT_RANKINGS_URL_PATTERN = FMS_API_URL_BASE + '/%s/rankings/%s'  # (year, event_short)
            self.FMS_API_EVENT_ALLIANCES_URL_PATTERN = FMS_API_URL_BASE + '/%s/alliances/%s'  # (year, event_short)
            self.FMS_API_TEAM_DETAILS_URL_PATTERN = FMS_API_URL_BASE + '/%s/teams/?teamNumber=%s'  # (year, teamNumber)
            self.FMS_API_TEAM_AVATAR_URL_PATTERN = FMS_API_URL_BASE + '/%s/avatars/?teamNumber=%s'  # (year, teamNumber)
            self.FMS_API_EVENT_AVATAR_URL_PATTERN = FMS_API_URL_BASE + '/%s/avatars/?eventCode=%s&page=%s'  # (year, eventCode, page)
            self.FMS_API_EVENT_LIST_URL_PATTERN = FMS_API_URL_BASE + '/%s/events'  # year
            self.FMS_API_EVENT_DETAILS_URL_PATTERN = FMS_API_URL_BASE + '/%s/events?eventCode=%s'  # (year, event_short)
            self.FMS_API_EVENTTEAM_LIST_URL_PATTERN = FMS_API_URL_BASE + '/%s/teams/?eventCode=%s&page=%s'  # (year, eventCode, page)
            self.FMS_API_DISTRICT_LIST_URL_PATTERN = FMS_API_URL_BASE + '/%s/districts'  # (year)
            self.FMS_API_DISTRICT_RANKINGS_PATTERN = FMS_API_URL_BASE + '/%s/rankings/district?districtCode=%s&page=%s'  # (year, district abbreviation, page)
        else:
            raise Exception("Unknown FMS API version: {}".format(version))

    def _get_event_short(self, event_short, event=None):
        # First, check if we've manually set the FRC API key
        if event and event.first_code:
            return event.first_code

        # Otherwise, check hard-coded exceptions
        return self.EVENT_SHORT_EXCEPTIONS.get(event_short, event_short)

    @ndb.tasklet
    def _parse_async(self, url, parser):
        # For URLFetches
        context = ndb.get_context()

        # Prep for saving/reading raw API response into/from cloudstorage
        gcs_dir_name = self.SAVED_RESPONSE_DIR_PATTERN.format(url.replace(self.FMS_API_DOMAIN, ''))
        if self._save_response and tba_config.CONFIG['save-frc-api-response']:
            try:
                gcs_dir_contents = cloudstorage.listbucket(gcs_dir_name)  # This is async
            except Exception, exception:
                logging.error("Error prepping for saving API response for: {}".format(url))
                logging.error(traceback.format_exc())
                gcs_dir_contents = []

        if self._sim_time:
            """
            Simulate FRC API response at a given time
            """
            content = None

            # Get list of responses
            file_prefix = 'frc-api-response/{}/'.format(url.replace(self.FMS_API_DOMAIN, ''))
            bucket_list_url = 'https://www.googleapis.com/storage/v1/b/bucket/o?bucket=tbatv-prod-hrd.appspot.com&prefix={}'.format(file_prefix)
            try:
                result = yield context.urlfetch(bucket_list_url)
            except Exception, e:
                logging.error("URLFetch failed for: {}".format(bucket_list_url))
                logging.info(e)
                raise ndb.Return(None)

            # Find appropriate timed response
            last_file_url = None
            for item in json.loads(result.content)['items']:
                filename = item['name']
                time_str = filename.replace(file_prefix, '').replace('.json', '').strip()
                file_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
                if file_time <= self._sim_time:
                    last_file_url = item['mediaLink']
                else:
                    break

            # Fetch response
            if last_file_url:
                try:
                    result = yield context.urlfetch(last_file_url)
                except Exception, e:
                    logging.error("URLFetch failed for: {}".format(last_file_url))
                    logging.info(e)
                    raise ndb.Return(None)
                content = result.content

            if content is None:
                raise ndb.Return(None)
            result = type('DummyResult', (object,), {"status_code": 200, "content": content})
        else:
            """
            Make fetch to FRC API
            """
            headers = {
                'Authorization': 'Basic {}'.format(self._fms_api_authtoken),
                'Accept': 'application/json',
                'Cache-Control': 'no-cache, max-age=10',
                'Pragma': 'no-cache',
            }
            try:
                result = yield context.urlfetch(url, headers=headers)
            except Exception, e:
                logging.error("URLFetch failed for: {}".format(url))
                logging.info(e)
                raise ndb.Return(None)

        old_status = self._is_down_sitevar.contents
        if result.status_code == 200:
            if old_status == True:
                self._is_down_sitevar.contents = False
                self._is_down_sitevar.put()
            ApiStatusController.clear_cache_if_needed(old_status, self._is_down_sitevar.contents)

            # Save raw API response into cloudstorage
            if self._save_response and tba_config.CONFIG['save-frc-api-response']:
                try:
                    # Check for last response
                    last_item = None
                    for last_item in gcs_dir_contents:
                        pass

                    write_new = True
                    if last_item is not None:
                        with cloudstorage.open(last_item.filename, 'r') as last_json_file:
                            if last_json_file.read() == result.content:
                                write_new = False  # Do not write if content didn't change

                    if write_new:
                        file_name = gcs_dir_name + '{}.json'.format(datetime.datetime.now())
                        with cloudstorage.open(file_name, 'w') as json_file:
                            json_file.write(result.content)
                except Exception, exception:
                    logging.error("Error saving API response for: {}".format(url))
                    logging.error(traceback.format_exc())
            try:
                json_content = json.loads(result.content.lstrip('\xef\xbb\xbf').rstrip('\x00'))
            except Exception, exception:
                logging.error("Error parsing: {}".format(url))
                logging.error(traceback.format_exc())
                raise ndb.Return(None)

            if type(parser) == list:
                raise ndb.Return([p.parse(json_content) for p in parser])
            else:
                raise ndb.Return(parser.parse(json_content))

        elif result.status_code % 100 == 5:
            # 5XX error - something is wrong with the server
            logging.warning('URLFetch for %s failed; Error code %s' % (url, result.status_code))
            if old_status == False:
                self._is_down_sitevar.contents = True
                self._is_down_sitevar.put()
            ApiStatusController.clear_cache_if_needed(old_status, self._is_down_sitevar.contents)
            raise ndb.Return(None)
        else:
            logging.warning('URLFetch for %s failed; Error code %s' % (url, result.status_code))
            raise ndb.Return(None)

    @ndb.toplevel
    def _parse(self, url, parser):
        result = yield self._parse_async(url, parser)
        raise ndb.Return(result)

    def getAwards(self, event):
        awards = []
        if event.event_type_enum == EventType.CMP_DIVISION and event.year >= 2015:  # 8 subdivisions from 2015+ have awards listed under 4 divisions
            event_team_keys = EventTeam.query(EventTeam.event == event.key).fetch(keys_only=True)
            valid_team_nums = set([int(etk.id().split('_')[1][3:]) for etk in event_team_keys])

            if event.year >= 2017:
                division = self.SUBDIV_TO_DIV_2017[event.event_short]
            else:
                division = self.SUBDIV_TO_DIV[event.event_short]
            awards += self._parse(self.FMS_API_AWARDS_URL_PATTERN % (event.year, self._get_event_short(division)), FMSAPIAwardsParser(event, valid_team_nums))

        awards += self._parse(self.FMS_API_AWARDS_URL_PATTERN % (event.year, self._get_event_short(event.event_short, event)), FMSAPIAwardsParser(event))
        return awards

    def getEventAlliances(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        alliances = self._parse(self.FMS_API_EVENT_ALLIANCES_URL_PATTERN % (year, self._get_event_short(event_short, event)), FMSAPIEventAlliancesParser())
        return alliances

    def getMatches(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        hs_parser = FMSAPIHybridScheduleParser(year, event_short)
        detail_parser = FMSAPIMatchDetailsParser(year, event_short)
        qual_matches_future = self._parse_async(self.FMS_API_HYBRID_SCHEDULE_QUAL_URL_PATTERN % (year, self._get_event_short(event_short, event)), hs_parser)
        playoff_matches_future = self._parse_async(self.FMS_API_HYBRID_SCHEDULE_PLAYOFF_URL_PATTERN % (year, self._get_event_short(event_short, event)), hs_parser)
        qual_details_future = self._parse_async(self.FMS_API_MATCH_DETAILS_QUAL_URL_PATTERN % (year, self._get_event_short(event_short, event)), detail_parser)
        playoff_details_future = self._parse_async(self.FMS_API_MATCH_DETAILS_PLAYOFF_URL_PATTERN % (year, self._get_event_short(event_short, event)), detail_parser)

        matches_by_key = {}
        qual_matches = qual_matches_future.get_result()
        if qual_matches is not None:
            for match in qual_matches[0]:
                matches_by_key[match.key.id()] = match
        playoff_matches = playoff_matches_future.get_result()
        if playoff_matches is not None:
            for match in playoff_matches[0]:
                matches_by_key[match.key.id()] = match

        qual_details = qual_details_future.get_result()
        qual_details_items = qual_details.items() if qual_details is not None else []
        playoff_details = playoff_details_future.get_result()
        playoff_details_items = playoff_details.items() if playoff_details is not None else []
        for match_key, match_details in qual_details_items + playoff_details_items:
            match_key = playoff_matches[1].get(match_key, match_key)
            if match_key in matches_by_key:
                matches_by_key[match_key].score_breakdown_json = json.dumps(match_details)

        return filter(
            lambda m: not FMSAPIHybridScheduleParser.is_blank_match(m),
            matches_by_key.values())

    def getEventRankings(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        result = self._parse(
            self.FMS_API_EVENT_RANKINGS_URL_PATTERN % (year, self._get_event_short(event_short, event)),
            [FMSAPIEventRankingsParser(year), FMSAPIEventRankings2Parser(year)])
        if result:
            return result
        else:
            return None, None

    def getTeamDetails(self, year, team_key):
        team_number = team_key[3:]  # everything after 'frc'

        result = self._parse(self.FMS_API_TEAM_DETAILS_URL_PATTERN % (year, team_number), FMSAPITeamDetailsParser(year))
        if result:
            return result[0]
        else:
            return None

    def getTeamAvatar(self, year, team_key):
        team_number = team_key[3:]  # everything after 'frc'

        avatars, keys_to_delete, _ = self._parse(self.FMS_API_TEAM_AVATAR_URL_PATTERN % (year, team_number), FMSAPITeamAvatarParser(year))
        if avatars:
            return avatars[0], keys_to_delete
        else:
            return None, keys_to_delete

    # Returns a tuple: (list(Event), list(District))
    def getEventList(self, year):
        result = self._parse(self.FMS_API_EVENT_LIST_URL_PATTERN % (year), FMSAPIEventListParser(year))
        if result:
            return result
        else:
            return [], []

    # Returns a list of districts
    def getDistrictList(self, year):
        result = self._parse(self.FMS_API_DISTRICT_LIST_URL_PATTERN % (year),
                             FMSAPIDistrictListParser(year))
        return result

    def getDistrictRankings(self, district_key):
        district = District.get_by_id(district_key)
        if not district:
            return None
        year = int(district_key[:4])
        district_short = district_key[4:]
        advancement = {}
        for page in range(1, 15):  # Ensure this won't loop forever
            url = self.FMS_API_DISTRICT_RANKINGS_PATTERN % (year, district_short.upper(), page)
            result = self._parse(url, FMSAPIDistrictRankingsParser(advancement))
            if not result:
                break
            advancement, more_pages = result

            if not more_pages:
                break

        district.advancement = advancement
        return [district]

    # Returns a tuple: (list(Event), list(District))
    def getEventDetails(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        api_event_short = self._get_event_short(event_short, event)
        result = self._parse(self.FMS_API_EVENT_DETAILS_URL_PATTERN % (year, api_event_short), FMSAPIEventListParser(year, short=event_short))
        if result:
            return result
        else:
            return [], []

    # Returns a list(Media)
    def getEventTeamAvatars(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        event = Event.get_by_id(event_key)
        parser = FMSAPITeamAvatarParser(year, short=event_short)
        api_event_short = self._get_event_short(event_short, event)
        avatars = []
        keys_to_delete = set()
        for page in range(1, 9):  # Ensure this won't loop forever. 8 pages should be more than enough
            url = self.FMS_API_EVENT_AVATAR_URL_PATTERN % (year, api_event_short, page)
            result = self._parse(url, parser)
            if result is None:
                break
            partial_avatars, partial_keys_to_delete, more_pages = result
            avatars.extend(partial_avatars)
            keys_to_delete = keys_to_delete.union(partial_keys_to_delete)

            if not more_pages:
                break

        return avatars, keys_to_delete

    # Returns list of tuples (team, districtteam, robot)
    def getEventTeams(self, event_key):
        year = int(event_key[:4])
        event_code = self._get_event_short(event_key[4:])

        event = Event.get_by_id(event_key)
        parser = FMSAPITeamDetailsParser(year)
        models = []  # will be list of tuples (team, districtteam, robot) model
        for page in range(1, 9):  # Ensure this won't loop forever. 8 pages should be more than enough
            url = self.FMS_API_EVENTTEAM_LIST_URL_PATTERN % (year, self._get_event_short(event_code, event), page)
            result = self._parse(url, parser)
            if result is None:
                break
            partial_models, more_pages = result
            models.extend(partial_models)

            if not more_pages:
                break

        return models
