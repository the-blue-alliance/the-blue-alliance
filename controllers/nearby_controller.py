import datetime
import logging
import tba_config

from google.appengine.api import search
from google.appengine.ext import ndb

from controllers.base_controller import CacheableHandler
from helpers.event_helper import EventHelper
from template_engine import jinja2_engine


class NearbyController(CacheableHandler):
    VALID_YEARS = list(reversed(range(1992, tba_config.MAX_YEAR + 1)))
    VALID_RANGES = [500, 1000, 5000]
    PAGE_SIZE = 20
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "near_me"  # (year, explicit_year)

    def _render(self):
        year = self.request.get('year', None)
        if not year:
            year = datetime.datetime.now().year
        location = self.request.get('location', None)
        range_limit = int(self.request.get('range_limit', self.VALID_RANGES[0]))
        page = int(self.request.get('page', 0))

        if location:
            lat, lon = EventHelper.get_lat_lon(location)

            dist_expr = 'distance(location, geopoint({}, {}))'.format(lat, lon)
            query_string = '{} < {} AND year={}'.format(dist_expr, range_limit * 1000, year)

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
            docs = search.Index(name="eventLocation").search(query)
            num_results = docs.number_found
            distances = {}
            event_keys = []
            for result in docs.results:
                distances[result.doc_id] = result.expressions[0].value
                event_keys.append(ndb.Key('Event', result.doc_id))

            events = ndb.get_multi(event_keys)
        else:
            num_results = 0
            events = []
            distances = []

        self.template_values.update({
            'valid_years': self.VALID_YEARS,
            'valid_ranges': self.VALID_RANGES,
            'page_size': self.PAGE_SIZE,
            'page': page,
            'year': year,
            'location': location,
            'range_limit': range_limit,
            'num_results': num_results,
            'events': events,
            'distances': distances,
        })

        return jinja2_engine.render('nearby.html', self.template_values)
