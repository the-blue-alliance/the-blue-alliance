from collections import defaultdict

from google.appengine.api import search
from google.appengine.ext import ndb

from consts.award_type import AwardType
from consts.event_type import EventType
from controllers.base_controller import CacheableHandler
from helpers.search_helper import SearchHelper
from models.event_team import EventTeam
from template_engine import jinja2_engine
import tba_config


SORT_ORDER = {
    AwardType.CHAIRMANS: 0,
    AwardType.ENGINEERING_INSPIRATION: 1,
    AwardType.WINNER: 2,
    AwardType.FINALIST: 3,
    AwardType.WOODIE_FLOWERS: 4,
}


class AdvancedSearchController(CacheableHandler):
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

    PAGE_SIZE = 20
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "advanced_search_{}_{}_{}_{}_{}_{}_{}"  # (year, award_types, event_type, time_period, robot_photo, cad_model, page)

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
        self._year = self._sanitize_int_param('year', 1992, tba_config.MAX_YEAR)

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

            self._time_period = self._sanitize_int_param('time_period', 0, 1)
        else:
            self._award_types = []
            self._event_type = -1
            self._time_period = 0

        self._robot_photo = self.request.get('robot_photo')
        if self._robot_photo:
            self._robot_photo = True
        self._cad_model = self.request.get('cad_model')
        if self._cad_model:
            self._cad_model = True

        self._page = self.request.get('page', 0)
        if not self._page or not self._page.isdigit():
            self._page = 0
        self._page = int(self._page)

    def get(self):
        self._get_params();
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(
            self._year, self._award_types, self._event_type, self._time_period,
            self._robot_photo, self._cad_model, self._page)
        super(AdvancedSearchController, self).get()

    def _render(self):
        new_search = not self._award_types and not self._robot_photo and not self._cad_model
        if new_search:
            result_models = []
            num_results = 0
            result_expressions = None
        else:
            # Construct query string
            sort_options_expressions = []
            returned_expressions = []
            partial_queries = []

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

            if self._award_types:
                if self._time_period == 0:
                    expression = 's_{}{}{}'.format(award_filter, event_type_filter, year_filter)
                elif self._time_period == 1:
                    expression = 'e_{}{}{}'.format(award_filter, event_type_filter, year_filter)
                partial_queries.append('{} > 0'.format(expression))

            if self._robot_photo:
                partial_queries.append('robot_photo_year = {}'.format(self._year))
            if self._cad_model:
                partial_queries.append('cad_model_year = {}'.format(self._year))

            query_string = ' AND ' .join(partial_queries)

            if self._award_types:
                sort_options_expressions += [
                    search.SortExpression(
                    expression=expression,
                    direction=search.SortExpression.DESCENDING)]
                returned_expressions += [
                    search.FieldExpression(
                        name='count',
                        expression=expression)]

            sort_options_expressions.append(
                search.SortExpression(
                    expression='number',
                    direction=search.SortExpression.ASCENDING))

            # Perform query
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
            result_expressions = defaultdict(lambda: defaultdict(float))
            for result in docs.results:
                team_key = result.doc_id.split('_')[0]
                model_keys.append(ndb.Key('Team', team_key))
                for expression in result.expressions:
                    result_expressions[team_key][expression.name] = expression.value

            model_futures = ndb.get_multi_async(model_keys)

            result_models = [model_future.get_result() for model_future in model_futures]

        self.template_values.update({
            'valid_years': self.VALID_YEARS,
            'valid_award_types': self.VALID_AWARD_TYPES,
            'num_special_awards': len(SORT_ORDER),
            'valid_event_types': self.VALID_EVENT_TYPES,
            'max_awards': SearchHelper.MAX_AWARDS,
            'page_size': self.PAGE_SIZE,
            'page': self._page,
            'year': self._year,
            'award_types': self._award_types,
            'event_type': self._event_type,
            'time_period': self._time_period,
            'robot_photo': self._robot_photo,
            'cad_model': self._cad_model,
            'new_search': new_search,
            'num_results': num_results,
            'result_models': result_models,
            'result_expressions': result_expressions,
        })

        return jinja2_engine.render('advanced_search.html', self.template_values)
