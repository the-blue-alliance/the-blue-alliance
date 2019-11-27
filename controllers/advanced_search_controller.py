from collections import defaultdict

from google.appengine.api import search
from google.appengine.ext import ndb

from consts.award_type import AwardType
from controllers.base_controller import CacheableHandler
from helpers.search_helper import SearchHelper
from models.event_team import EventTeam
from template_engine import jinja2_engine
import tba_config


SORT_ORDER = {
    AwardType.CHAIRMANS: 0,
    AwardType.ENGINEERING_INSPIRATION: 1,
    AwardType.WOODIE_FLOWERS: 4,
}


class AdvancedSearchController(CacheableHandler):
    VALID_YEARS = list(reversed(tba_config.VALID_YEARS))

    VALID_AWARD_TYPES = [kv for kv in AwardType.SEARCHABLE.items()]
    VALID_AWARD_TYPES = sorted(
        VALID_AWARD_TYPES,
        key=lambda (event_type, name): SORT_ORDER.get(event_type, name))

    VALID_SEEDS = [8, 4, 2, 1]
    PLAYOFF_MAP = {
        1: 'sf',
        2: 'f',
        3: 'win',
    }

    PAGE_SIZE = 20
    MAX_RESULTS = 1000
    VALID_SORT_FIELDS = {'team', 'seed', 'playoff_level'}

    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "advanced_search_{}_{}_{}_{}_{}_{}"  # (year, award_types, seed, playoff_level, cad_model, page)

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
        self._year = self._sanitize_int_param('year', tba_config.MIN_YEAR, tba_config.MAX_YEAR)

        self._award_types = self.request.get_all('award_type')
        if self._award_types:
            # Sort to make caching more likely
            self._award_types = filter(lambda x: x in AwardType.SEARCHABLE, sorted(set([
                int(award_type) if award_type.isdigit() else None
                for award_type in self._award_types])))
        else:
            self._award_types = []

        self._seed = self.request.get('seed')
        if not self._seed or not self._seed.isdigit():
            self._seed = 0
        self._seed = int(self._seed)
        if self._seed not in self.VALID_SEEDS:
            self._seed = 0

        self._playoff_level = self._sanitize_int_param('playoff_level', 0, 3)

        self._cad_model = self.request.get('cad_model')
        if self._cad_model:
            self._cad_model = True
        else:
            self._cad_model = False

        self._page = self.request.get('page', 0)
        if not self._page or not self._page.isdigit():
            self._page = 0
        self._page = int(self._page)
        self._page = min(self._page, self.MAX_RESULTS / self.PAGE_SIZE - 1)

        self._sort_field = self.request.get('sort_field')
        if self._sort_field not in self.VALID_SORT_FIELDS:
            self._sort_field = 'team'

    def get(self):
        self._get_params();
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(
            self._year, self._award_types, self._seed, self._playoff_level, self._cad_model, self._page)
        super(AdvancedSearchController, self).get()

    def _render(self):
        new_search = not self._year or (not self._award_types and not self._seed and not self._playoff_level and not self._cad_model)
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

            partial_queries.append('year={}'.format(self._year))
            award_filter = ' OR '.join(['award={}'.format(award_type) for award_type in self._award_types])
            if award_filter:
                partial_queries.append(award_filter)

            if self._seed:
                seed_field_name = 'seed_{}'.format(self._seed)
                partial_queries.append('{}>0'.format(seed_field_name))
                returned_expressions.append(search.FieldExpression(
                    name='seed_count', expression=seed_field_name))

                if self._sort_field == 'seed':
                    sort_options_expressions.append(
                        search.SortExpression(
                            expression=seed_field_name,
                            direction=search.SortExpression.DESCENDING))

            if self._playoff_level:
                comp_level_name = 'comp_level_{}'.format(self.PLAYOFF_MAP[self._playoff_level])
                partial_queries.append('{}>0'.format(comp_level_name))
                returned_expressions.append(search.FieldExpression(
                    name='comp_level_count', expression=comp_level_name))

                if self._sort_field == 'playoff_level':
                    sort_options_expressions.append(
                        search.SortExpression(
                            expression=comp_level_name,
                            direction=search.SortExpression.DESCENDING))

            if self._cad_model:
                partial_queries.append('has_cad=1')

            query_string = ' AND ' .join(partial_queries)

            # Tiebreak sorting by number
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
            'valid_seeds': self.VALID_SEEDS,
            'seed': self._seed,
            'playoff_level': self._playoff_level,
            'page_size': self.PAGE_SIZE,
            'max_results': self.MAX_RESULTS,
            'page': self._page,
            'year': self._year,
            'award_types': self._award_types,
            'cad_model': self._cad_model,
            'new_search': new_search,
            'num_results': num_results,
            'capped_num_results': min(self.MAX_RESULTS, num_results),
            'result_models': result_models,
            'result_expressions': result_expressions,
            'sort_field': self._sort_field,
        })

        return jinja2_engine.render('advanced_search.html', self.template_values)
