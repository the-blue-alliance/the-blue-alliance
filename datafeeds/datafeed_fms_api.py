import base64
import json
import logging

from google.appengine.api import urlfetch

from datafeeds.datafeed_base import DatafeedBase

from models.sitevar import Sitevar

from parsers.fms_api.fms_api_awards_parser import FMSAPIAwardsParser
from parsers.fms_api.fms_api_event_alliances_parser import FMSAPIEventAlliancesParser
from parsers.fms_api.fms_api_event_rankings_parser import FMSAPIEventRankingsParser
from parsers.fms_api.fms_api_hybrid_schedule_parser import FMSAPIHybridScheduleParser
from parsers.fms_api.fms_api_team_details_parser import FMSAPITeamDetailsParser


class DatafeedFMSAPI(object):
    FMS_API_URL_BASE = 'https://frc-api.usfirst.org/api/v1.0'

    FMS_API_AWARDS_URL_PATTERN = FMS_API_URL_BASE + '/awards/%s/%s'  # (year, event_short)
    FMS_API_HYBRID_SCHEDULE_QUAL_URL_PATTERN = FMS_API_URL_BASE + '/schedule/%s/%s/qual/hybrid'  # (year, event_short)
    FMS_API_HYBRID_SCHEDULE_PLAYOFF_URL_PATTERN = FMS_API_URL_BASE + '/schedule/%s/%s/playoff/hybrid'  # (year, event_short)
    FMS_API_EVENT_RANKINGS_URL_PATTERN = FMS_API_URL_BASE + '/rankings/%s/%s'  # (year, event_short)
    FMS_API_EVENT_ALLIANCES_URL_PATTERN = FMS_API_URL_BASE + '/alliances/%s/%s'  # (year, event_short)
    FMS_API_TEAM_DETAILS_URL_PATTERN = FMS_API_URL_BASE + '/api/v1.0/teams/%s/?teamNumber=%s'  # (year, teamNumber)

    def __init__(self, *args, **kw):
        fms_api_secrets = Sitevar.get_by_id('fmsapi.secrets')
        if fms_api_secrets is None:
            raise Exception("Missing sitevar: fmsapi.secrets. Can't access FMS API.")

        fms_api_username = fms_api_secrets.contents['username']
        fms_api_authkey = fms_api_secrets.contents['authkey']
        self._fms_api_authtoken = base64.b64encode('{}:{}'.format(fms_api_username, fms_api_authkey))

    def _parse(self, url, parser):
        headers = {
            'Authorization': 'Basic {}'.format(self._fms_api_authtoken)
        }
        try:
            result = urlfetch.fetch(url,
                                    headers=headers,
                                    deadline=5)
        except Exception, e:
            logging.error("URLFetch failed for: {}".format(url))
            logging.info(e)
            return None

        if result.status_code == 200:
            return parser.parse(json.loads(result.content))
        else:
            logging.warning('URLFetch for %s failed; Error code %s' % (url, result.status_code))
            return None

    def getAwards(self, event):
        awards = self._parse(self.FMS_API_AWARDS_URL_PATTERN % (event.year, event.event_short), FMSAPIAwardsParser(event))
        return awards

    def getEventAlliances(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        alliances = self._parse(self.FMS_API_EVENT_ALLIANCES_URL_PATTERN % (year, event_short), FMSAPIEventAlliancesParser())
        return alliances

    def getMatches(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        parser = FMSAPIHybridScheduleParser(year, event_short)
        qual_matches = self._parse(self.FMS_API_HYBRID_SCHEDULE_QUAL_URL_PATTERN % (year, event_short), parser)
        playoff_matches = self._parse(self.FMS_API_HYBRID_SCHEDULE_PLAYOFF_URL_PATTERN % (year, event_short), parser)

        matches = []
        if qual_matches is not None:
            matches += qual_matches
        if playoff_matches is not None:
            matches += playoff_matches

        return matches

    def getEventRankings(self, event_key):
        year = int(event_key[:4])
        event_short = event_key[4:]

        rankings = self._parse(self.FMS_API_EVENT_RANKINGS_URL_PATTERN % (year, event_short), FMSAPIEventRankingsParser())
        return rankings

    def getTeamDetails(self, year, team_key):
        team_number = team_key[3:]  # everything after 'frc'

        team = self._parse(self.FMS_API_TEAM_DETAILS_URL_PATTERN % (year, team_number), FMSAPITeamDetailsParser())
        return team
