import base64
import json
import logging

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from consts.event_type import EventType
from controllers.api.api_status_controller import ApiStatusController
from datafeeds.datafeed_base import DatafeedBase

from models.event_team import EventTeam
from models.sitevar import Sitevar

from parsers.fms_api.fms_api_awards_parser import FMSAPIAwardsParser
from parsers.fms_api.fms_api_event_alliances_parser import FMSAPIEventAlliancesParser
from parsers.fms_api.fms_api_event_list_parser import FMSAPIEventListParser
from parsers.fms_api.fms_api_event_rankings_parser import FMSAPIEventRankingsParser
from parsers.fms_api.fms_api_match_parser import FMSAPIHybridScheduleParser, FMSAPIMatchDetailsParser
from parsers.fms_api.fms_api_team_details_parser import FMSAPITeamDetailsParser


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

    def __init__(self, version):
        fms_api_secrets = Sitevar.get_by_id('fmsapi.secrets')
        if fms_api_secrets is None:
            raise Exception("Missing sitevar: fmsapi.secrets. Can't access FMS API.")

        fms_api_username = fms_api_secrets.contents['username']
        fms_api_authkey = fms_api_secrets.contents['authkey']
        self._fms_api_authtoken = base64.b64encode('{}:{}'.format(fms_api_username, fms_api_authkey))

        self._is_down_sitevar = Sitevar.get_by_id('apistatus.fmsapi_down')
        if not self._is_down_sitevar:
            self._is_down_sitevar = Sitevar(id="apistatus.fmsapi_down", description="Is FMSAPI down?")

        if version == 'v1.0':
            FMS_API_URL_BASE = 'https://frc-api.firstinspires.org/api/v1.0'
            self.FMS_API_AWARDS_URL_PATTERN = FMS_API_URL_BASE + '/awards/%s/%s'  # (year, event_short)
            self.FMS_API_HYBRID_SCHEDULE_QUAL_URL_PATTERN = FMS_API_URL_BASE + '/schedule/%s/%s/qual/hybrid'  # (year, event_short)
            self.FMS_API_HYBRID_SCHEDULE_PLAYOFF_URL_PATTERN = FMS_API_URL_BASE + '/schedule/%s/%s/playoff/hybrid'  # (year, event_short)
            self.FMS_API_EVENT_RANKINGS_URL_PATTERN = FMS_API_URL_BASE + '/rankings/%s/%s'  # (year, event_short)
            self.FMS_API_EVENT_ALLIANCES_URL_PATTERN = FMS_API_URL_BASE + '/alliances/%s/%s'  # (year, event_short)
            self.FMS_API_TEAM_DETAILS_URL_PATTERN = FMS_API_URL_BASE + '/teams/%s/?teamNumber=%s'  # (year, teamNumber)
            self.FMS_API_EVENT_LIST_URL_PATTERN = FMS_API_URL_BASE + '/events/season=%s'
            self.FMS_API_EVENTTEAM_LIST_URL_PATTERN = FMS_API_URL_BASE + '/teams/?season=%s&eventCode=%s&page=%s'  # (year, eventCode, page)
        elif version == 'v2.0':
            FMS_API_URL_BASE = 'https://frc-api.firstinspires.org/v2.0'
            self.FMS_API_AWARDS_URL_PATTERN = FMS_API_URL_BASE + '/%s/awards/%s'  # (year, event_short)
            self.FMS_API_HYBRID_SCHEDULE_QUAL_URL_PATTERN = FMS_API_URL_BASE + '/%s/schedule/%s/qual/hybrid'  # (year, event_short)
            self.FMS_API_HYBRID_SCHEDULE_PLAYOFF_URL_PATTERN = FMS_API_URL_BASE + '/%s/schedule/%s/playoff/hybrid'  # (year, event_short)
            self.FMS_API_MATCH_DETAILS_QUAL_URL_PATTERN = FMS_API_URL_BASE + '/%s/scores/%s/qual'  # (year, event_short)
            self.FMS_API_MATCH_DETAILS_PLAYOFF_URL_PATTERN = FMS_API_URL_BASE + '/%s/scores/%s/playoff'  # (year, event_short)
            self.FMS_API_EVENT_RANKINGS_URL_PATTERN = FMS_API_URL_BASE + '/%s/rankings/%s'  # (year, event_short)
            self.FMS_API_EVENT_ALLIANCES_URL_PATTERN = FMS_API_URL_BASE + '/%s/alliances/%s'  # (year, event_short)
            self.FMS_API_TEAM_DETAILS_URL_PATTERN = FMS_API_URL_BASE + '/%s/teams/?teamNumber=%s'  # (year, teamNumber)
            self.FMS_API_EVENT_LIST_URL_PATTERN = FMS_API_URL_BASE + '/%s/events'  # year
            self.FMS_API_EVENTTEAM_LIST_URL_PATTERN = FMS_API_URL_BASE + '/%s/teams/?eventCode=%s&page=%s'  # (year, eventCode, page)
        else:
            raise Exception("Unknown FMS API version: {}".format(version))

    def _get_event_short(self, event_short):
        return self.EVENT_SHORT_EXCEPTIONS.get(event_short, event_short)

    @ndb.tasklet
    def _parse_async(self, url, parser):
        headers = {
            'Authorization': 'Basic {}'.format(self._fms_api_authtoken),
            'Cache-Control': 'no-cache, max-age=10',
            'Pragma': 'no-cache',
        }
        try:
            rpc = urlfetch.create_rpc(deadline=10)
            result = yield urlfetch.make_fetch_call(rpc, url, headers=headers)
        except Exception, e:
            logging.error("URLFetch failed for: {}".format(url))
            logging.info(e)
            raise ndb.Return(None)

        old_status = self._is_down_sitevar.contents
        if result.status_code == 200:
            self._is_down_sitevar.contents = False
            self._is_down_sitevar.put()
            ApiStatusController.clear_cache_if_needed(old_status, self._is_down_sitevar.contents)
            raise ndb.Return(parser.parse(json.loads(result.content)))
        elif result.status_code % 100 == 5:
            # 5XX error - something is wrong with the server
            logging.warning('URLFetch for %s failed; Error code %s' % (url, result.status_code))
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

        awards += self._parse(self.FMS_API_AWARDS_URL_PATTERN % (event.year, self._get_event_short(event.event_short)), FMSAPIAwardsParser(event))
        return awards

    def getEventAlliances(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        alliances = self._parse(self.FMS_API_EVENT_ALLIANCES_URL_PATTERN % (year, self._get_event_short(event_short)), FMSAPIEventAlliancesParser())
        return alliances

    def getMatches(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        hs_parser = FMSAPIHybridScheduleParser(year, event_short)
        detail_parser = FMSAPIMatchDetailsParser(year, event_short)
        qual_matches_future = self._parse_async(self.FMS_API_HYBRID_SCHEDULE_QUAL_URL_PATTERN % (year, self._get_event_short(event_short)), hs_parser)
        playoff_matches_future = self._parse_async(self.FMS_API_HYBRID_SCHEDULE_PLAYOFF_URL_PATTERN % (year, self._get_event_short(event_short)), hs_parser)
        qual_details_future = self._parse_async(self.FMS_API_MATCH_DETAILS_QUAL_URL_PATTERN % (year, self._get_event_short(event_short)), detail_parser)
        playoff_details_future = self._parse_async(self.FMS_API_MATCH_DETAILS_PLAYOFF_URL_PATTERN % (year, self._get_event_short(event_short)), detail_parser)

        matches_by_key = {}
        qual_matches = qual_matches_future.get_result()
        if qual_matches is not None:
            for match in qual_matches:
                matches_by_key[match.key.id()] = match
        playoff_matches = playoff_matches_future.get_result()
        if playoff_matches is not None:
            for match in playoff_matches:
                matches_by_key[match.key.id()] = match

        qual_details = qual_details_future.get_result()
        qual_details_items = qual_details.items() if qual_details is not None else []
        playoff_details = playoff_details_future.get_result()
        playoff_details_items = playoff_details.items() if playoff_details is not None else []
        for match_key, match_details in qual_details_items + playoff_details_items:
            if match_key in matches_by_key:
                matches_by_key[match_key].score_breakdown_json = json.dumps(match_details)

        return matches_by_key.values()

    def getEventRankings(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        rankings = self._parse(self.FMS_API_EVENT_RANKINGS_URL_PATTERN % (year, self._get_event_short(event_short)), FMSAPIEventRankingsParser(year))
        return rankings

    def getTeamDetails(self, year, team_key):
        team_number = team_key[3:]  # everything after 'frc'

        result = self._parse(self.FMS_API_TEAM_DETAILS_URL_PATTERN % (year, team_number), FMSAPITeamDetailsParser(year))
        if result:
            return result[0]  # (team, districtteam, robot)
        else:
            return None

    def getEventList(self, year):
        events = self._parse(self.FMS_API_EVENT_LIST_URL_PATTERN % (year), FMSAPIEventListParser(year))
        return events

    # Returns list of tuples (team, districtteam, robot)
    def getEventTeams(self, event_key):
        year = int(event_key[:4])
        event_code = self._get_event_short(event_key[4:])
        if event_code == 'cmp':  # Don't add cmp teams because FIRST serves all Championship teams under Einstein
            return []

        parser = FMSAPITeamDetailsParser(year)
        models = []  # will be list of tuples (team, districtteam, robot) model
        for page in range(1, 9):  # Ensure this won't loop forever. 8 pages should be more than enough
            url = self.FMS_API_EVENTTEAM_LIST_URL_PATTERN % (year, event_code, page)
            result = self._parse(url, parser)
            if result is None:
                break
            partial_models, more_pages = result
            models.extend(partial_models)

            if not more_pages:
                break

        return models
