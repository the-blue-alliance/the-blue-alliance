import datetime
import logging
import tba_config

from google.appengine.api import search
from google.appengine.ext import ndb

from controllers.base_controller import CacheableHandler
from helpers.location_helper import LocationHelper
from models.event_team import EventTeam
from template_engine import jinja2_engine


class NearbyController(CacheableHandler):
    VALID_YEARS = list(reversed(range(1992, tba_config.MAX_YEAR + 1)))
    VALID_RANGES = [250, 500, 2500]
    DEFAULT_SEARCH_TYPE = 'teams'
    PAGE_SIZE = 20
    METERS_PER_MILE = 5280 * 12 * 2.54 / 100
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "nearby_{}_{}_{}_{}_{}"  # (year, location, range_limit, search_type, page)

    def __init__(self, *args, **kw):
        super(NearbyController, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _get_params(self):
        year = self.request.get('year', None)
        if not year:
            year = datetime.datetime.now().year
        year = int(year)
        location = self.request.get('location', None)
        range_limit = int(self.request.get('range_limit', self.VALID_RANGES[0]))
        if range_limit not in self.VALID_RANGES:
            range_limit = self.VALID_RANGES[0]
        search_type = self.request.get('search_type', self.DEFAULT_SEARCH_TYPE)
        if search_type != 'teams' and search_type != 'events':
            search_type = self.DEFAULT_SEARCH_TYPE
        page = int(self.request.get('page', 0))

        return year, location, range_limit, search_type, page

    def get(self):
        year, location, range_limit, search_type, page = self._get_params()
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(year, location, range_limit, search_type, page)
        super(NearbyController, self).get()

    def _render(self):
        year, location, range_limit, search_type, page = self._get_params()

        num_results = 0
        results = []
        distances = []
        if location:
            lat_lon, _ = LocationHelper.get_lat_lon(location)
            if lat_lon:
                lat, lon = lat_lon

                dist_expr = 'distance(location, geopoint({}, {}))'.format(lat, lon)
                if search_type == 'teams':
                    query_string = '{} < {}'.format(dist_expr, range_limit * self.METERS_PER_MILE)
                else:
                    query_string = '{} < {} AND year={}'.format(dist_expr, range_limit * self.METERS_PER_MILE, year)

                offset = self.PAGE_SIZE * page

                query = search.Query(
                    query_string=query_string,
                    options=search.QueryOptions(
                        limit=self.PAGE_SIZE,
                        offset=offset,
                        sort_options=search.SortOptions(
                            expressions=[
                                search.SortExpression(
                                    expression=dist_expr,
                                    direction=search.SortExpression.ASCENDING
                                )
                            ]
                        ),
                        returned_expressions=[
                            search.FieldExpression(
                                name='distance',
                                expression=dist_expr
                            )
                        ],
                    )
                )
                if search_type == 'teams':
                    search_index = search.Index(name="teamLocation")
                else:
                    search_index = search.Index(name="eventLocation")

                docs = search_index.search(query)
                num_results = docs.number_found
                distances = {}
                keys = []
                event_team_count_futures = {}
                for result in docs.results:
                    distances[result.doc_id] = result.expressions[0].value / self.METERS_PER_MILE
                    if search_type == 'teams':
                        event_team_count_futures[result.doc_id] = EventTeam.query(
                            EventTeam.team == ndb.Key('Team', result.doc_id),
                            EventTeam.year == year).count_async(limit=1, keys_only=True)
                        keys.append(ndb.Key('Team', result.doc_id))
                    else:
                        keys.append(ndb.Key('Event', result.doc_id))

                result_futures = ndb.get_multi_async(keys)

                if search_type == 'teams':
                    results = []
                    for result_future, team_key in zip(result_futures, keys):
                        if event_team_count_futures[team_key.id()].get_result() != 0:
                            results.append(result_future.get_result())

                else:
                    results = [result_future.get_result() for result_future in result_futures]

        self.template_values.update({
            'valid_years': self.VALID_YEARS,
            'valid_ranges': self.VALID_RANGES,
            'page_size': self.PAGE_SIZE,
            'page': page,
            'year': year,
            'location': location,
            'range_limit': range_limit,
            'search_type': search_type,
            'num_results': num_results,
            'results': results,
            'distances': distances,
        })

        return jinja2_engine.render('nearby.html', self.template_values)
