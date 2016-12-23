import logging
import tba_config

from google.appengine.api import search
from google.appengine.ext import ndb

from consts.award_type import AwardType
from consts.event_type import EventType
from controllers.base_controller import CacheableHandler
from helpers.location_helper import LocationHelper
from helpers.search_helper import SearchHelper
from models.event_team import EventTeam
from template_engine import jinja2_engine


SORT_ORDER = {
    AwardType.CHAIRMANS: 0,
    AwardType.ENGINEERING_INSPIRATION: 1,
    AwardType.WINNER: 2,
    AwardType.FINALIST: 3,
    AwardType.WOODIE_FLOWERS: 4,
}


class AdvancedSearchController(CacheableHandler):
    VALID_RANGES = [100, 500]  # Miles
    VALID_YEARS = list(reversed(range(1992, tba_config.MAX_YEAR + 1)))

    VALID_AWARD_TYPES = [kv for kv in AwardType.SEARCHABLE.items()]
    VALID_AWARD_TYPES = sorted(
        VALID_AWARD_TYPES,
        key=lambda (event_type, name): SORT_ORDER.get(event_type, name))

    VALID_EVENT_TYPES = [
        (EventType.REGIONAL, 'Regional'),
        (EventType.DISTRICT, 'District'),
        (EventType.DISTRICT_CMP, 'District Championship'),
        (EventType.CMP_DIVISION, 'Championship Division'),
        (EventType.CMP_FINALS, 'Championship'),
    ]

    DEFAULT_SEARCH_TYPE = 'teams'
    PAGE_SIZE = 20
    METERS_PER_MILE = 5280 * 12 * 2.54 / 100
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "advanced_search_{}_{}_{}_{}_{}_{}_{}_{}"  # (year, award_type, event_type, location, search_type, sort_field, sort_desc, page)

    def __init__(self, *args, **kw):
        super(AdvancedSearchController, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24

    def _sanitize_int_param(self, param_name, min_val, max_val):
        """
        Restricts a parameter to be within min_val and max_val
        Returns 0 otherwise
        """
        param = self.request.get(param_name)
        if not param or not param.isdigit():
            param = 0
        param = int(param)
        if param < min_val or param > max_val:
            param = 0
        return param

    def _get_params(self):
        # Parse and sanitize inputs
        self._location_type = self._sanitize_int_param('location_type', 0, len(self.VALID_RANGES))

        self._location = self.request.get('location')

        self._year = self._sanitize_int_param('year', 1992, tba_config.MAX_YEAR)

        self._filter_type = self._sanitize_int_param('filter_type', 0, 2)
        if self._filter_type == 0:
            self._year = self._sanitize_int_param('year', 1992, tba_config.MAX_YEAR)
            self._award_types = []
            self._event_type = -1
            self._time_period = 0
        elif self._filter_type == 2:
            self._award_types = self.request.get('award_type', allow_multiple=True)
            if self._award_types:
                # Sort to make caching more likely
                self._award_types = filter(lambda x: x in AwardType.SEARCHABLE, sorted(set([
                    int(award_type) if award_type.isdigit() else None
                    for award_type in self._award_types])))[:SearchHelper.MAX_AWARDS]
                self._event_type = self.request.get('event_type')
                if self._event_type:
                    self._event_type = int(self._event_type) if self._event_type.isdigit() else -1
                else:
                    self._event_type = -1
                if self._event_type not in [x[0] for x in self.VALID_EVENT_TYPES]:
                    self._event_type = -1

                self._time_period = self._sanitize_int_param('time_period', 0, 2)
                if self._time_period == 0:
                    self._year = 0
            else:
                self._award_types = []
                self._event_type = -1
                self._time_period = 0
                self._year = 0

        # if self.request.get('sort_desc'):
        #     sort_desc = True
        # else:
        #     sort_desc = False

        # sort_field = self.request.get('sort_field')
        # if sort_field:
        #     sort_field = int(sort_field)
        # else:
        #     sort_field = 0  # Default to team number

        # location = self.request.get('location', '')
        # search_type = self.request.get('search_type', self.DEFAULT_SEARCH_TYPE)
        # if search_type != 'teams' and search_type != 'events':
        #     search_type = self.DEFAULT_SEARCH_TYPE
        self._page = self.request.get('page', 0)
        if not self._page or not self._page.isdigit():
            self._page = 0
        self._page = int(self._page)

    def get(self):
        self._get_params();
        # # year, award_types, event_types, location, search_type, sort_field, sort_desc, page = self._get_params()
        # self._partial_cache_key = self.CACHE_KEY_FORMAT.format(year, award_types, event_types, location, search_type, sort_field, sort_desc, page)
        super(AdvancedSearchController, self).get()

    def _render(self):
        # Construct query string
        if self._filter_type == 0:  # Year filter
            search_index = search.Index(name=SearchHelper.TEAM_AWARDS_INDEX)
        elif self._filter_type == 2:  # Award filter
            search_index = search.Index(name=SearchHelper.TEAM_AWARDS_INDEX)

            award_filter = '_'.join(['a{}'.format(award_type) for award_type in self._award_types])

            if self._event_type == -1:
                event_type_filter = ''
            else:
                event_type_filter = '_e{}'.format(self._event_type)

            if self._year:
                year_filter = '_y{}'.format(self._year)
            else:
                year_filter = ''

            if self._time_period == 0:
                expression = 'o_{}{}{}'.format(award_filter, event_type_filter, year_filter)
            elif self._time_period == 1:
                expression = 's_{}{}{}'.format(award_filter, event_type_filter, year_filter)
            elif self._time_period == 2:
                expression = 'e_{}{}{}'.format(award_filter, event_type_filter, year_filter)
            query_string = '{} > 0'.format(expression)

            logging.info(query_string)

            if self._time_period == 0:
                sort_options_expressions = []
                returned_expressions = []
            else:
                sort_expression = ' + '.join(expressions)
                logging.info(sort_expression)
                sort_options_expressions = [
                    search.SortExpression(
                    expression=sort_expression,
                    direction=search.SortExpression.DESCENDING,
                    default_value=0)]
                returned_expressions = []
                # returned_expressions = [
                #     search.FieldExpression(
                #         name='count',
                #         expression='number')]

        sort_options_expressions.append(
            search.SortExpression(
                expression='number',
                direction=search.SortExpression.ASCENDING))

        # Perform query
        logging.info(query_string)
        query = search.Query(
            query_string=query_string,
            options=search.QueryOptions(
                limit=self.PAGE_SIZE,
                number_found_accuracy=10000,  # Larger than the number of possible results
                offset=self.PAGE_SIZE * self._page,
                ids_only=True,
                sort_options=search.SortOptions(
                    expressions=sort_options_expressions
                ),
                returned_expressions=returned_expressions
            )
        )

        docs = search_index.search(query)
        num_results = docs.number_found
        model_keys = []
        for result in docs.results:
            logging.info(result)
            model_keys.append(ndb.Key('Team', result.doc_id.split('_')[0]))

        model_futures = ndb.get_multi_async(model_keys)

        result_models = [model_future.get_result() for model_future in model_futures]

        # year, award_types, event_types, location, search_type, sort_field, sort_desc, page = self._get_params()

        # num_results = 0
        # results = []
        # distances = []

        # query_string = 'year={}'.format(year)
        # returned_fields = ['bb_count']
        # num_fields = 1
        # query_type = None
        # if award_types and event_types:
        #     query_type = 'event_award'
        #     num_fields += len(award_types) * len(event_types)
        #     for award_type in award_types:
        #         for event_type in event_types:
        #             field = 'event_award_{}_{}_count'.format(event_type, award_type)
        #             query_string += ' AND {} > 0'.format(field, event_type, award_type)
        #             returned_fields.append(field)
        # elif award_types:
        #     query_type = 'award'
        #     num_fields += len(award_types)
        #     for award_type in award_types:
        #         field = 'award_{}_count'.format(award_type)
        #         query_string += ' AND {} > 0'.format(field, award_type)
        #         returned_fields.append(field)

        # sort_options_expressions = [
        #     search.SortExpression(
        #         expression='number',
        #         direction=search.SortExpression.DESCENDING if (sort_field == 0 and sort_desc) else search.SortExpression.ASCENDING
        #     )]
        # returned_expressions = []

        # if sort_field != 0 and sort_field <= len(returned_fields):
        #     sort_options_expressions.insert(0, search.SortExpression(
        #         expression=returned_fields[sort_field - 1],
        #         direction=search.SortExpression.ASCENDING if sort_desc else search.SortExpression.DESCENDING
        #     ))

        # if location:
        #     lat_lon = LocationHelper.get_lat_lng(location)
        #     if lat_lon:
        #         num_fields += 1
        #         returned_fields.append('distance')
        #         lat, lon = lat_lon
        #         dist_expr = 'distance(location, geopoint({}, {}))'.format(lat, lon)
        #         query_string = '{} > {} AND year={}'.format(dist_expr, -1, year)

        #         if sort_field == num_fields:
        #             sort_options_expressions = [
        #                 search.SortExpression(
        #                     expression=dist_expr,
        #                     direction=search.SortExpression.DESCENDING if sort_desc else search.SortExpression.ASCENDING
        #                 )]

        #         returned_expressions = [
        #             search.FieldExpression(
        #                 name='distance',
        #                 expression=dist_expr
        #             )]

        # if sort_field > len(returned_fields):
        #     sort_field = 0

        # query = search.Query(
        #     query_string=query_string,
        #     options=search.QueryOptions(
        #         limit=self.PAGE_SIZE,
        #         number_found_accuracy=10000,  # Larger than the number of possible results
        #         offset=self.PAGE_SIZE * page,
        #         returned_fields=returned_fields,
        #         sort_options=search.SortOptions(
        #             expressions=sort_options_expressions
        #         ),
        #         returned_expressions=returned_expressions
        #     )
        # )
        # if search_type == 'teams':
        #     search_index = search.Index(name="teamYear")
        # else:
        #     search_index = search.Index(name="eventLocation")

        # docs = search_index.search(query)
        # num_results = docs.number_found
        # distances = {}
        # keys = []
        # all_fields = []
        # for result in docs.results:
        #     key = result.doc_id.split('_')[0]

        #     # Save fields
        #     fields = {}
        #     for field in result.fields:
        #         fields[field.name] = field.value

        #     # Save distances
        #     if location and lat_lon:
        #         fields['distance'] = result.expressions[0].value / self.METERS_PER_MILE

        #     all_fields.append(fields)

        #     if search_type == 'teams':
        #         keys.append(ndb.Key('Team', key))
        #     else:
        #         keys.append(ndb.Key('Event', key))

        # result_futures = ndb.get_multi_async(keys)

        # # Construct field names
        # field_names = []
        # for field in returned_fields:
        #     if field == 'bb_count':
        #         field_names.append('# Blue Banner')
        #     elif field == 'distance':
        #         field_names.append('Distance')
        #     else:
        #         if query_type == 'event_award':
        #             split = field.split('_')
        #             event_type = int(split[2])
        #             award_type = int(split[3])

        #             if event_type == 3:  # TODO don't hardcode
        #                 event_str = 'Championship Division'
        #             elif event_type == 4:
        #                 event_str = 'Championship'

        #             field_names.append('# {} {}'.format(event_str, AwardType.SEARCHABLE.get(award_type)))
        #         elif query_type == 'award':
        #             award_type = int(field.split('_')[1])
        #             field_names.append('# {}'.format(AwardType.SEARCHABLE.get(award_type)))

        # results = zip([result_future.get_result() for result_future in result_futures], all_fields)

        self.template_values.update({
            'valid_ranges': self.VALID_RANGES,
            'valid_years': self.VALID_YEARS,
            'valid_award_types': self.VALID_AWARD_TYPES,
            'num_special_awards': len(SORT_ORDER),
            'valid_event_types': self.VALID_EVENT_TYPES,
            'max_awards': SearchHelper.MAX_AWARDS,
            # 'page_size': self.PAGE_SIZE,
            # 'page': page,
            'location_type': self._location_type,
            'location': self._location,
            'filter_type': self._filter_type,
            'year': self._year,
            'award_types': self._award_types,
            'event_type': self._event_type,
            'time_period': self._time_period,
            # 'search_type': search_type,
            'num_results': num_results,
            'result_models': result_models,
            # 'returned_fields': returned_fields,
            # 'field_names': field_names,
            # 'sort_field': sort_field,
            # 'sort_desc': sort_desc,
        })

        return jinja2_engine.render('advanced_search.html', self.template_values)
