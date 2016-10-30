import datetime
import logging
import tba_config

from google.appengine.api import search
from google.appengine.ext import ndb

from controllers.base_controller import CacheableHandler
from helpers.event_helper import EventHelper
from models.event_team import EventTeam
from template_engine import jinja2_engine


class NearbyController(CacheableHandler):
    VALID_YEARS = list(reversed(range(1992, tba_config.MAX_YEAR + 1)))
    VALID_RANGES = [500, 1000, 5000]
    DEFAULT_SEARCH_TYPE = 'teams'
    PAGE_SIZE = 20
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "near_me"  # (year, explicit_year)

    def _render(self):
        year = self.request.get('year', None)
        if not year:
            year = datetime.datetime.now().year
        year = int(year)
        location = self.request.get('location', None)
        range_limit = int(self.request.get('range_limit', self.VALID_RANGES[0]))
        search_type = self.request.get('search_type', self.DEFAULT_SEARCH_TYPE)
        if search_type != 'teams' and search_type != 'events':
            search_type = self.DEFAULT_SEARCH_TYPE
        page = int(self.request.get('page', 0))

        if location:
            lat, lon = EventHelper.get_lat_lon(location)

            dist_expr = 'distance(location, geopoint({}, {}))'.format(lat, lon)
            if search_type == 'teams':
                query_string = '{} < {}'.format(dist_expr, range_limit * 1000)
            else:
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
                distances[result.doc_id] = result.expressions[0].value
                if search_type == 'teams':
                    event_team_count_futures[result.doc_id] = EventTeam.query(
                        EventTeam.team == ndb.Key('Team', result.doc_id),
                        EventTeam.year == year).count_async(limit=1, keys_only=True)
                    keys.append(ndb.Key('Team', result.doc_id))
                else:
                    keys.append(ndb.Key('Event', result.doc_id))

            results = ndb.get_multi(keys)

            if search_type == 'teams':
                results = filter(lambda team: event_team_count_futures[team.key.id()].get_result() != 0, results)
        else:
            num_results = 0
            results = []
            distances = []

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
