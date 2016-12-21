import datetime
import logging
import tba_config

from google.appengine.api import search
from google.appengine.ext import ndb

from consts.award_type import AwardType
from consts.event_type import EventType
from controllers.base_controller import CacheableHandler
from helpers.location_helper import LocationHelper
from models.event_team import EventTeam
from template_engine import jinja2_engine


class NearbyController(CacheableHandler):
    VALID_YEARS = list(reversed(range(1992, tba_config.MAX_YEAR + 1)))
    VALID_AWARD_TYPES = [
        (AwardType.CHAIRMANS, 'Chairman\'s'),
        (AwardType.ENGINEERING_INSPIRATION, 'Engineering Inspiration'),
        (AwardType.WINNER, 'Event Winner'),
        (AwardType.FINALIST, 'Event Finalist'),
        (AwardType.WOODIE_FLOWERS, 'Woodie Flowers'),
    ]
    VALID_EVENT_TYPES = [
        (EventType.CMP_DIVISION, 'Championship Division'),
        (EventType.CMP_FINALS, 'Einstein Field'),
    ]
    DEFAULT_SEARCH_TYPE = 'teams'
    PAGE_SIZE = 20
    METERS_PER_MILE = 5280 * 12 * 2.54 / 100
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "nearby_{}_{}_{}_{}_{}_{}"  # (year, award_type, event_type, location, search_type, page)

    def __init__(self, *args, **kw):
        super(NearbyController, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _get_params(self):
        year = self.request.get('year', None)
        if not year:
            year = datetime.datetime.now().year
        year = int(year)

        award_type = self.request.get('award_type')
        if award_type:
            award_type = int(award_type)
        else:
            award_type = ''

        event_type = self.request.get('event_type')
        if event_type:
            event_type = int(event_type)
        else:
            event_type = ''

        location = self.request.get('location', '')
        search_type = self.request.get('search_type', self.DEFAULT_SEARCH_TYPE)
        if search_type != 'teams' and search_type != 'events':
            search_type = self.DEFAULT_SEARCH_TYPE
        page = int(self.request.get('page', 0))

        return year, award_type, event_type, location, search_type, page

    def get(self):
        year, award_type, event_type, location, search_type, page = self._get_params()
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(year, award_type, event_type, location, search_type, page)
        super(NearbyController, self).get()

    def _render(self):
        year, award_type, event_type, location, search_type, page = self._get_params()
        logging.info((year, award_type, event_type, location, search_type, page))

        num_results = 0
        results = []
        distances = []

        sort_options_expressions = [
            search.SortExpression(
                expression='number',
                direction=search.SortExpression.ASCENDING
            )]
        returned_expressions = []

        query_string = 'year={}'.format(year)
        if location:
            lat_lon = LocationHelper.get_lat_lng(location)
            if lat_lon:
                lat, lon = lat_lon
                dist_expr = 'distance(location, geopoint({}, {}))'.format(lat, lon)
                query_string = '{} > {} AND year={}'.format(dist_expr, -1, year)

                sort_options_expressions = [
                    search.SortExpression(
                        expression=dist_expr,
                        direction=search.SortExpression.ASCENDING
                    )]

                returned_expressions = [
                    search.FieldExpression(
                        name='distance',
                        expression=dist_expr
                    )]

        if award_type != '' and event_type != '':
            query_string += ' AND event_award_type = {}_{}'.format(event_type, award_type)
        elif award_type != '':
            query_string += ' AND award_type = {}'.format(award_type)
        elif event_type != '':
            query_string += ' AND event_type = {}'.format(event_type)

        offset = self.PAGE_SIZE * page

        query = search.Query(
            query_string=query_string,
            options=search.QueryOptions(
                limit=self.PAGE_SIZE,
                number_found_accuracy=10000,  # Larger than the number of possible results
                offset=offset,
                returned_fields=['bb_count'],
                sort_options=search.SortOptions(
                    expressions=sort_options_expressions
                ),
                returned_expressions=returned_expressions
            )
        )
        if search_type == 'teams':
            search_index = search.Index(name="teamYear")
        else:
            search_index = search.Index(name="eventLocation")

        docs = search_index.search(query)
        num_results = docs.number_found
        distances = {}
        bb_count = {}
        keys = []
        for result in docs.results:
            logging.info(result)
            key = result.doc_id.split('_')[0]
            bb_count[key] = result.fields[0].value
            if location and lat_lon:
                distances[key] = result.expressions[0].value / self.METERS_PER_MILE
            if search_type == 'teams':
                keys.append(ndb.Key('Team', key))
            else:
                keys.append(ndb.Key('Event', key))

        result_futures = ndb.get_multi_async(keys)
        results = [result_future.get_result() for result_future in result_futures]

        self.template_values.update({
            'valid_years': self.VALID_YEARS,
            'valid_award_types': self.VALID_AWARD_TYPES,
            'valid_event_types': self.VALID_EVENT_TYPES,
            'page_size': self.PAGE_SIZE,
            'page': page,
            'year': year,
            'award_type': award_type,
            'event_type': event_type,
            'location': location,
            'search_type': search_type,
            'num_results': num_results,
            'results': results,
            'bb_count': bb_count,
            'distances': distances,
        })

        return jinja2_engine.render('advanced_search.html', self.template_values)
