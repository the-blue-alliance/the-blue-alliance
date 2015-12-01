import base64
import json
import logging

from google.appengine.api import urlfetch

from consts.event_type import EventType
from datafeeds.datafeed_base import DatafeedBase

from models.event_team import EventTeam

from parsers.first_elasticsearch.first_elasticsearch_event_list_parser import FIRSTElasticSearchEventListParser


class DatafeedFIRSTElasticSearch(object):
    EVENT_SHORT_EXCEPTIONS = {
        'arc': 'archimedes',
        'cars': 'carson',
        'carv': 'carver',
        'cur': 'curie',
        'gal': 'galileo',
        'hop': 'hopper',
        'new': 'newton',
        'tes': 'tesla',
    }

    SUBDIV_TO_DIV = {
        'arc': 'cmp-arte',
        'cars': 'cmp-gaca',
        'carv': 'cmp-cuca',
        'cur': 'cmp-cuca',
        'gal': 'cmp-gaca',
        'hop': 'cmp-neho',
        'new': 'cmp-neho',
        'tes': 'cmp-arte',
    }

    def __init__(self):
        URL_BASE = 'http://es01.usfirst.org'
        self.EVENT_LIST_URL_PATTERN = URL_BASE + '/events/_search?size=1000&source={"query":{"query_string":{"query":"(event_type:FRC)%20AND%20(event_season:%s)"}}}'  # (year)
        self.EVENT_DETAILS_URL_PATTERN = URL_BASE + '/events/_search?size=1&source={"query":{"query_string":{"query":"_id:%s"}}}'  # (first_eid)
        self.EVENT_TEAMS_URL_PATTERN = URL_BASE + '/teams/_search?size=1000&source={"partial_fields":{"partial1":{"exclude":["awards","events"]}},"query":{"query_string":{"query":"events.fk_events:%s"}}}'  # (first_eid)
        self.TEAM_DETAILS_URL_PATTERN = URL_BASE + '/teams/_search?size=1&source={"query":{"query_string":{"query":"_id:%s"}}}'  # (first_tpid)

    def _get_event_short(self, event_short):
        return self.EVENT_SHORT_EXCEPTIONS.get(event_short, event_short)

    def _parse(self, url, parser):
        headers = {
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

    def getEventList(self, year):
        events = self._parse(self.FMS_API_EVENT_LIST_URL_PATTERN % (year), FMSAPIEventListParser(year))
        return events

    def getEventDetails(self, event):
        return

    def getEventTeams(self, event):
        return

    def getTeamDetails(self, team):
        return

    # def getTeamDetails(self, year, team_key):
    #     team_number = team_key[3:]  # everything after 'frc'

    #     team = self._parse(self.FMS_API_TEAM_DETAILS_URL_PATTERN % (year, team_number), FMSAPITeamDetailsParser(year))
    #     return team

    # def getEventList(self, year):
    #     events = self._parse(self.FMS_API_EVENT_LIST_URL_PATTERN % (year), FMSAPIEventListParser(year))
    #     return events

    # # Returns list of tuples (team, districtteam, robot)
    # def getEventTeams(self, event_key):
    #     year = int(event_key[:4])
    #     event_code = event_key[4:]
    #     parser = FMSAPITeamDetailsParser(year)
    #     models = []  # will be list of tuples (team, districtteam, robot) model
    #     for page in range(1, 9):  # Ensure this won't loop forever. 8 pages should be more than enough
    #         url = self.FMS_API_EVENTTEAM_LIST_URL_PATTERN % (year, event_code, page)
    #         result = self._parse(url, parser)
    #         if result is None:
    #             break
    #         partial_models, more_pages = result
    #         models.extend(partial_models)

    #         if not more_pages:
    #             break

    #     return models
