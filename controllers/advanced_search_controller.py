from collections import defaultdict

from google.appengine.api import search
from google.appengine.ext import ndb

from consts.award_type import AwardType
from controllers.base_controller import CacheableHandler
from helpers.search_helper import SearchHelper
from models.event_team import EventTeam
from template_engine import jinja2_engine
import tba_config
from models.match import Match


SORT_ORDER = {
    AwardType.CHAIRMANS: 0,
    AwardType.ENGINEERING_INSPIRATION: 1,
    AwardType.WOODIE_FLOWERS: 4,
}


class AdvancedTeamSearchController(CacheableHandler):
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
        super(AdvancedTeamSearchController, self).__init__(*args, **kw)
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
        self._get_params()
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(
            self._year, self._award_types, self._seed, self._playoff_level, self._cad_model, self._page)
        super(AdvancedTeamSearchController, self).get()

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

        return jinja2_engine.render('advanced_team_search.html', self.template_values)


class AdvancedMatchSearchController(CacheableHandler):
    VALID_YEARS = list(reversed(range(1992, tba_config.MAX_YEAR + 1)))

    VALID_COMP_LEVELS = [
        ('qm', 'Qualifications'),
        ('ef', 'Octofinals'),
        ('qf', 'Quarterfinals'),
        ('sf', 'Semifinals'),
        ('f', 'Finals')
    ]

    PAGE_SIZE = 50
    MAX_RESULTS = 1000
    VALID_SORT_FIELDS = {'event', 'match'}

    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "advanced_match_search_{}_{}_{}_{}_{}_{}_{}"  # (year, own_alliance, opp_alliance, event_key, comp_levels, video, page)

    def __init__(self, *args, **kw):
        super(AdvancedMatchSearchController, self).__init__(*args, **kw)
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

    def _parse_alliance(self, param_name):
        """
        Return a list of teams generated from an alliance string, such as
        "2521, 254, 997"
        """
        param = self.request.get(param_name)
        teams = filter(None, [team.strip() for team in param.split(',')])
        return teams

    def _get_params(self):
        # Parse and sanitize inputs
        self._year = self._sanitize_int_param('year', 1992, tba_config.MAX_YEAR)

        self._own_alliance = self._parse_alliance('own_alliance')
        self._opp_alliance = self._parse_alliance('opp_alliance')
        self._event_key = self.request.get('event_key')
        self._comp_levels = self.request.get_all('comp_level')

        self._video = self.request.get('video')
        if self._video:
            self._video = True
        else:
            self._video = False

        self._page = self.request.get('page', 0)
        if not self._page or not self._page.isdigit():
            self._page = 0
        self._page = int(self._page)
        self._page = min(self._page, self.MAX_RESULTS / self.PAGE_SIZE - 1)

        self._sort_field = self.request.get('sort_field')
        if self._sort_field not in self.VALID_SORT_FIELDS:
            self._sort_field = 'match'

    def get(self):
        self._get_params()
        self._partial_cache_key = self.CACHE_KEY_FORMAT.format(
            self._year, ','.join(self._own_alliance), ','.join(self._opp_alliance), self._event_key,
            ','.join(self._comp_levels), self._video, self._page)
        super(AdvancedMatchSearchController, self).get()

    def _render(self):
        new_search = not self._year
        if new_search:
            match_results = []
            num_results = 0
        else:
            # Construct query string
            partial_queries = []

            search_1 = []
            search_2 = []

            for team in self._own_alliance:
                search_1.append(Match.blue_alliance_team == 'frc{}'.format(team))
                search_2.append(Match.red_alliance_team == 'frc{}'.format(team))

            for team in self._opp_alliance:
                search_1.append(Match.red_alliance_team == 'frc{}'.format(team))
                search_2.append(Match.blue_alliance_team == 'frc{}'.format(team))

            if len(search_1) > 0:
                partial_queries.append(ndb.OR(ndb.AND(*search_1), ndb.AND(*search_2)))

            if self._year is not None:
                partial_queries.append(Match.year == self._year)

            if self._event_key is not None:
                partial_queries.append(Match.event == ndb.Key('Event', self._event_key))

            if len(self._comp_levels) > 0:
                partial_queries.append(Match.comp_level.IN(self._comp_levels))

            if self._video:
                partial_queries.append(Match.has_video == True)

            matches, _, _ = Match.query(*partial_queries).order(Match.play_order_sort).order(Match._key).fetch_page(self.PAGE_SIZE, offset=self.PAGE_SIZE * self._page)

            num_results = len(matches)
            event_model_keys = []
            for match in matches:
                event_model_keys.append(match.event)

            event_model_futures = ndb.get_multi_async(event_model_keys)
            event_result_models = [model_future.get_result() for model_future in event_model_futures]

            match_results = []
            for n, model in enumerate(matches):
                model.match_key = model.key.id()
                model.event_model = event_result_models[n]
                match_results.append(model)

        self.template_values.update({
            'valid_years': self.VALID_YEARS,
            'valid_comp_levels': self.VALID_COMP_LEVELS,
            'num_special_awards': len(SORT_ORDER),
            'page_size': self.PAGE_SIZE,
            'max_results': self.MAX_RESULTS,
            'page': self._page,
            'year': self._year,
            'own_alliance': ', '.join(self._own_alliance),
            'opp_alliance': ', '.join(self._opp_alliance),
            'event_key': self._event_key,
            'comp_levels': self._comp_levels,
            'video': self._video,
            'searched_teams': self._own_alliance + self._opp_alliance,
            'new_search': new_search,
            'num_results': num_results,
            'capped_num_results': min(self.MAX_RESULTS, num_results),
            'result_models': match_results,
            'sort_field': self._sort_field,
        })

        return jinja2_engine.render('advanced_match_search.html', self.template_values)
