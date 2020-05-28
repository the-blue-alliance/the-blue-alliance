from collections import defaultdict
import copy
import math
import numpy as np
import time

from consts.event_type import EventType
from database.event_query import TeamYearEventsQuery
from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper
from helpers.matchstats_helper import MatchstatsHelper
from models.event_details import EventDetails
from models.match import Match


class ContributionCalculator(object):
    def __init__(self, event, matches, stat, default_mean, default_var):
        """
        stat: 'score' or a specific breakdown like 'auto_points' or 'boulders'
        """
        self._event = event
        self._matches = matches
        self._stat = stat
        self._default_mean = default_mean
        self._default_var = default_var

        self._team_list, self._team_id_map = self._build_team_mapping()

        # Setup matrices
        m = len(self._matches)
        t = len(self._team_list)
        self._Ao = np.zeros((2*m, t))  # Match teams
        self._Mmean = np.zeros((2*m, 1))  # Means
        self._Mvar = np.zeros((2*m, 1))  # Variances

        # Past event stats for initialization
        self._past_stats_mean, self._past_stats_var = self._get_past_stats(self._event, self._team_list)

        # For finding event averages for initialization
        self._mean_sums = []
        self._var_sums = []

        # These aren't used to persist state, just allocating space
        self._Oe = np.zeros((t, 1))  # Prior estimates
        self._diags = np.ndarray(t)  # Prior estimates variances

        # Things to return
        self._means = {}
        self._vars = {}

    def _build_team_mapping(self):
        """
        Returns (team_list, team_id_map)
        team_list: A list of team_str such as 'frc254' or 'frc254B'
        team_id_map: A dict of key: team_str, value: row index in x_matrix that corresponds to the team
        """
        # Build team list
        team_list = set()
        for match in self._matches:
            for alliance_color in ['red', 'blue']:
                for team in match.alliances[alliance_color]['teams']:
                    team_list.add(team)

        team_list = list(team_list)
        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        return team_list, team_id_map

    def _get_past_stats(self, cur_event, team_list):
        past_stats_mean = defaultdict(list)  # team key > values
        past_stats_var = defaultdict(list)  # team key > values

        no_priors_team_list = team_list

        for year_diff in xrange(1):
            team_events_futures = []
            for team in no_priors_team_list:
                team_events_futures.append((team, TeamYearEventsQuery(team, cur_event.year - year_diff).fetch_async()))

            no_priors_team_list = []
            for team, events_future in team_events_futures:
                events = events_future.get_result()
                EventHelper.sort_events(events)
                no_past_mean = True
                for event in events:
                    if event.event_type_enum in EventType.SEASON_EVENT_TYPES and \
                            event.start_date < cur_event.start_date and \
                            event.event_type_enum != EventType.CMP_FINALS and \
                            event.details:
                        # event.details is backed by in-context cache
                        predictions = event.details.predictions
                        if predictions and predictions.get('stat_mean_vars') and predictions['stat_mean_vars'].get('qual'):
                            if team in predictions['stat_mean_vars']['qual'].get(self._stat, {}).get('mean', []):
                                team_mean = predictions['stat_mean_vars']['qual'][self._stat]['mean'][team]
                                if year_diff != 0:
                                    team_mean *= 1  # TODO: Hacky; scale based on actual data
                                past_stats_mean[team].append(team_mean)
                                no_past_mean = False
                            if team in predictions['stat_mean_vars']['qual'].get(self._stat, {}).get('var', []):
                                team_var = predictions['stat_mean_vars']['qual'][self._stat]['var'][team]
                                if year_diff != 0:
                                    team_var = self._default_var * 3  # TODO: Hacky; scale based on actual data
                                past_stats_var[team].append(team_var)
                if no_past_mean:
                    no_priors_team_list.append(team)

        return past_stats_mean, past_stats_var

    def _normpdf(self, x, mu, sigma):
        x = float(x)
        mu = float(mu)
        sigma = float(sigma)
        u = (x-mu)/abs(sigma)
        y = (1.0/(np.sqrt(2.0*np.pi)*abs(sigma)))*np.exp(-u*u/2.0)
        return y

    def calculate_before_match(self, i):
        # Used for both mean and var
        AoT = self._Ao.transpose()
        Aoo = np.dot(AoT, self._Ao)

        ####################################################################
        # Estimate Team Means
        # Populate priors
        for team in self._team_list:
            mean = self._default_mean
            if team in self._past_stats_mean:
                # Use team's past means
                mean = 0
                weight_sum = 0
                for j, o in enumerate(reversed(self._past_stats_mean[team])):
                    weight = pow(0.1, j)
                    mean += weight * o
                    weight_sum += weight
                mean /= weight_sum
            else:
                if self._past_stats_mean:
                    # Use averages from other past teams
                    mean = np.mean([ato[-1] for ato in self._past_stats_mean.values()])
                elif self._mean_sums:
                    # Use averages from this event
                    mean = np.mean(self._mean_sums) / 3

            self._Oe[self._team_id_map[team]] = mean
            self._diags[self._team_id_map[team]] = 3  # TODO

        # MMSE Contribution Mean
        Omean = np.linalg.inv(Aoo + np.diag(self._diags)).dot(AoT.dot(self._Mmean) + np.diag(self._diags).dot(self._Oe))
        for team, Omean in zip(self._team_list, Omean):
            self._means[team] = Omean[0]

        ####################################################################
        # Estimate Team Variances
        # Populate priors
        for team in self._team_list:
            var = self._default_var
            if team in self._past_stats_var:
                # Use team's past variances
                var = 0
                weight_sum = 0
                for j, o in enumerate(reversed(self._past_stats_var[team])):
                    weight = pow(0.1, j)
                    var += weight * o
                    weight_sum += weight
                var /= weight_sum
            # else:
            #     if self._past_stats_var:
            #         # Use averages from other past teams
            #         var = np.mean([ato[-1] for ato in self._past_stats_var.values()])
            #     elif self._var_sums:
            #         # Use averages from this event
            #         var = np.mean(self._var_sums) / 3

            self._Oe[self._team_id_map[team]] = var
            self._diags[self._team_id_map[team]] = 3  # TODO

        # MMSE Contribution Variance
        Ovar = abs(np.linalg.inv(Aoo + np.diag(self._diags)).dot(AoT.dot(self._Mvar) + np.diag(self._diags).dot(self._Oe)))
        for team, stat in zip(self._team_list, Ovar):
            self._vars[team] = stat[0]

        ####################################################################
        # Add results for next iter
        match = self._matches[i]
        if match.has_been_played and match.score_breakdown:
            means = {}
            for color in ['red', 'blue']:
                if self._stat == 'score':
                    score = match.alliances[color]['score']
                    # Subtract bonus objective scores for playoffs, since they are accounted for explicitly
                    # 2016; these should be zero for qual matches
                    score -= match.score_breakdown[color].get('breachPoints', 0)
                    score -= match.score_breakdown[color].get('capturePoints', 0)
                    # 2017; these should be zero for qual matches
                    score -= match.score_breakdown[color].get('kPaBonusPoints', 0)
                    score -= match.score_breakdown[color].get('rotorBonusPoints', 0)
                    means[color] = score
                elif self._stat == 'auto_points':
                    means[color] = match.score_breakdown[color]['autoPoints']
                elif self._stat == 'boulders':
                    means[color] = (
                        match.score_breakdown[color].get('autoBouldersLow', 0) +
                        match.score_breakdown[color].get('autoBouldersHigh', 0) +
                        match.score_breakdown[color].get('teleopBouldersLow', 0) +
                        match.score_breakdown[color].get('teleopBouldersHigh', 0))
                elif self._stat == 'crossings':
                    means[color] = (
                        match.score_breakdown[color].get('position1crossings', 0) +
                        match.score_breakdown[color].get('position2crossings', 0) +
                        match.score_breakdown[color].get('position3crossings', 0) +
                        match.score_breakdown[color].get('position4crossings', 0) +
                        match.score_breakdown[color].get('position5crossings', 0))
                elif self._stat == 'pressure':
                    means[color] = (
                        float(match.score_breakdown[color].get('autoFuelHigh', 0)) +
                        float(match.score_breakdown[color].get('autoFuelLow', 0)) / 3 +
                        float(match.score_breakdown[color].get('teleopFuelHigh', 0)) / 3 +
                        float(match.score_breakdown[color].get('teleopFuelLow', 0)) / 9)
                elif self._stat == 'gears':
                    # Guess gears from rotors.
                    if match.score_breakdown[color].get('rotor4Engaged'):
                        num_gears = 12
                    elif match.score_breakdown[color].get('rotor3Engaged'):
                        num_gears = 6
                    elif match.score_breakdown[color].get('rotor2Auto'):
                        num_gears = 3
                    elif match.score_breakdown[color].get('rotor2Engaged'):
                        num_gears = 2
                    elif match.score_breakdown[color].get('rotor1Auto'):
                        num_gears = 1
                    elif match.score_breakdown[color].get('rotor1Engaged'):
                        num_gears = 0  # Free gear
                    else:
                        num_gears = -1  # Failed to place reserve gear
                    means[color] = num_gears
                elif self._stat == 'endgame_points':
                    means[color] = match.score_breakdown[color]['endgamePoints']
                elif self._stat == 'rocket_pieces_scored':
                    count = 0
                    for side1 in ['Far', 'Near']:
                        for side2 in ['Left', 'Right']:
                            for level in ['low', 'mid', 'top']:
                                position = match.score_breakdown[color]['{}{}Rocket{}'.format(level, side2, side1)]
                                if 'Cargo' in position:
                                    count += 2
                                elif 'Panel' in position:
                                    count += 1
                    means[color] = count
                elif self._stat == 'hab_climb_points':
                    means[color] = match.score_breakdown[color]['habClimbPoints']
                elif self._stat == 'power_cells_scored':
                    count = 0
                    for mode in ['auto', 'teleop']:
                        for goal in ['Bottom', 'Outer', 'Inner']:
                            count += match.score_breakdown[color]['{}Cells{}'.format(mode, goal)]
                    means[color] = count
                else:
                    raise Exception("Unknown stat: {}".format(self._stat))

            self._Mmean[2*i] = means['red']
            self._Mmean[2*i+1] = means['blue']

            self._mean_sums.append(means['red'])
            self._mean_sums.append(means['blue'])

            predicted_mean_red = 0
            for team in match.alliances['red']['teams']:
                self._Ao[2*i, self._team_id_map[team]] = 1
                predicted_mean_red += self._means[team]

            predicted_mean_blue = 0
            for team in match.alliances['blue']['teams']:
                self._Ao[2*i+1, self._team_id_map[team]] = 1
                predicted_mean_blue += self._means[team]

            # Find max of prob over var_sum
            best_prob = 0
            best_var_sum = None
            var_sum = 1.0
            var_sum_step = 2.0**12
            while var_sum > 0 and var_sum_step >= 1:
                prob = self._normpdf(means['red'], predicted_mean_red, np.sqrt(var_sum))
                if prob >= best_prob:
                    best_prob = prob
                    best_var_sum = var_sum
                prob2 = self._normpdf(means['red'], predicted_mean_red, np.sqrt(var_sum+1))
                if prob2 >= best_prob:
                    best_prob = prob2
                    best_var_sum = var_sum+1
                if prob2 > prob:
                    var_sum += var_sum_step
                else:
                    var_sum -= var_sum_step
                var_sum_step /= 2
            self._Mvar[2*i] = best_var_sum
            self._var_sums.append(best_var_sum)

            # Optimize prob over var_sum for max
            best_prob = 0
            best_var_sum = None
            var_sum = 1.0
            var_sum_step = 2.0**12
            while var_sum > 0 and var_sum_step >= 1:
                prob = self._normpdf(means['blue'], predicted_mean_blue, np.sqrt(var_sum))
                if prob >= best_prob:
                    best_prob = prob
                    best_var_sum = var_sum
                prob2 = self._normpdf(means['blue'], predicted_mean_blue, np.sqrt(var_sum+1))
                if prob2 >= best_prob:
                    best_prob = prob2
                    best_var_sum = var_sum+1
                if prob2 > prob:
                    var_sum += var_sum_step
                else:
                    var_sum -= var_sum_step
                var_sum_step /= 2
            self._Mvar[2*i+1] = best_var_sum
            self._var_sums.append(best_var_sum)

        return {'mean': self._means, 'var': self._vars}


class PredictionHelper(object):
    @classmethod
    def _normcdf(cls, x):
        return (1.0 + math.erf(x / np.sqrt(2.0))) / 2.0

    @classmethod
    def _predict_match(cls, event, match, stat_mean_vars, is_playoff):
        mean_vars = {
            'red': defaultdict(lambda: defaultdict(int)),
            'blue': defaultdict(lambda: defaultdict(int)),
        }
        for color in ['red', 'blue']:
            for team in match.alliances[color]['teams']:
                for stat, mean_var in stat_mean_vars.items():
                    team_mean = mean_var['mean'][team]
                    team_var = mean_var['var'][team]

                    # Crossing OPR usually underestimates. hacky fix to make numbers more believable
                    if stat == 'crossings':
                        team_mean = max(0, team_mean) * 1.2

                    mean_vars[color][stat]['mean'] += team_mean
                    mean_vars[color][stat]['var'] += team_var

        prediction = {
            'red': {
                'score': mean_vars['red']['score']['mean'],
                'score_var': mean_vars['red']['score']['var'],
            },
            'blue': {
                'score': mean_vars['blue']['score']['mean'],
                'score_var': mean_vars['blue']['score']['var'],
            },
        }

        # Year specific
        for stat in stat_mean_vars.keys():
            for color in ['red', 'blue']:
                if stat != 'score':
                    prediction[color][stat] = mean_vars[color][stat]['mean']
                    prediction[color]['{}_var'.format(stat)] = mean_vars[color][stat]['var']
                # 2016
                if stat == 'boulders':
                    # Prob capture
                    tower_strength = 10 if (event.event_type_enum in EventType.CMP_EVENT_TYPES or event.key.id() == '2016cc') else 8

                    mu = mean_vars[color][stat]['mean'] - tower_strength
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_capture'] = prob

                    # Playoff Bonus
                    if is_playoff:
                        prediction[color]['score'] += prob * 25
                        prob_int = int(prob * 100)
                        prediction[color]['score_var'] += np.var([0] * (100 - prob_int) + [25] * prob_int)

                elif stat == 'crossings':
                    # Prob breach
                    crossings_to_breach = 8

                    mu = mean_vars[color][stat]['mean'] - crossings_to_breach
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_breach'] = prob

                    # Playoff Bonus
                    if is_playoff:
                        prediction[color]['score'] += prob * 20
                        prob_int = int(prob * 100)
                        prediction[color]['score_var'] += np.var([0] * (100 - prob_int) + [20] * prob_int)
                # 2017
                if stat == 'pressure':
                    required_pressure = 40

                    mu = mean_vars[color][stat]['mean'] - required_pressure
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_pressure'] = prob

                    # Playoff Bonus
                    if is_playoff:
                        prediction[color]['score'] += prob * 20
                        prob_int = int(prob * 100)
                        prediction[color]['score_var'] += np.var([0] * (100 - prob_int) + [20] * prob_int)
                if stat == 'gears':
                    requried_gears = 12

                    mu = mean_vars[color][stat]['mean'] - requried_gears
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_gears'] = prob

                    # Playoff Bonus
                    if is_playoff:
                        prediction[color]['score'] += prob * 100
                        prob_int = int(prob * 100)
                        prediction[color]['score_var'] += np.var([0] * (100 - prob_int) + [100] * prob_int)
                # 2018
                if stat == 'auto_points':
                    required_auto = 25  # 15 auto run + 5 seconds of ownership

                    mu = mean_vars[color][stat]['mean'] - required_auto
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_auto_quest'] = prob
                if stat == 'endgame_points':
                    required_endgame = 60  #

                    mu = mean_vars[color][stat]['mean'] - required_endgame
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_face_boss'] = prob
                # 2019
                if stat == 'rocket_pieces_scored':
                    required_pieces = 12

                    mu = mean_vars[color][stat]['mean'] - required_pieces
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_complete_rocket'] = prob
                if stat == 'hab_climb_points':
                    required_points = 15

                    mu = mean_vars[color][stat]['mean'] - required_points
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_hab_docking'] = prob
                # 2020
                if stat == 'power_cells_scored':
                    required_pieces = 49

                    mu = mean_vars[color][stat]['mean'] - required_pieces
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_shield_energized'] = prob
                if stat == 'endgame_points':
                    required_points = 65

                    mu = mean_vars[color][stat]['mean'] - required_points
                    prob = 1 - cls._normcdf(-mu / np.sqrt(mean_vars[color][stat]['var']))
                    prediction[color]['prob_shield_operational'] = prob

        # Prob win
        red_score = prediction['red']['score']
        blue_score = prediction['blue']['score']
        red_score_var = prediction['red']['score_var']
        blue_score_var = prediction['blue']['score_var']

        mu = abs(red_score - blue_score)
        prob = 1 - cls._normcdf(-mu / np.sqrt(red_score_var + blue_score_var))
        if math.isnan(prob):
            prob = 0.5

        if red_score > blue_score:
            winning_alliance = 'red'
        elif blue_score > red_score:
            winning_alliance = 'blue'
        else:
            winning_alliance = 'red'  # Choose red if predicted tie

        prediction['winning_alliance'] = winning_alliance
        prediction['prob'] = prob

        return prediction

    @classmethod
    def get_match_predictions(cls, matches):
        if not matches:
            return None, None, None
        predictions = {
            'qual': {},
            'playoff': {},
        }
        prediction_stats = {
            'qual': {},
            'playoff': {},
        }
        stat_mean_vars = {
            'qual': {},
            'playoff': {},
        }
        event_key = matches[0].event
        event = event_key.get()
        if event.year == 2016:
            relevant_stats = [
                ('score', 20, 10**2),
                ('auto_points', 20, 10**2),
                ('crossings', 0, 1**2),
                ('boulders', 0, 1**2),
            ]
        elif event.year == 2017:
            relevant_stats = [
                ('score', 50, 30**2),
                ('pressure', 0, 1**2),
                ('gears', 0, 1**2),
            ]
        elif event.year == 2018:
            relevant_stats = [
                ('score', 50, 30**2),
                ('auto_points', 0, 1**2),
                ('endgame_points', 0, 1**2),
            ]
        elif event.year == 2019:
            relevant_stats = [
                ('score', 10, 20**2),
                ('rocket_pieces_scored', 1, 3**2),
                ('hab_climb_points', 2, 3**2),
            ]
        elif event.year == 2020:
            relevant_stats = [
                ('score', 0, 50**2),
                ('power_cells_scored', 0, 20**2),
                ('endgame_points', 0, 20**2),
            ]

        contribution_calculators = [ContributionCalculator(event, matches, s, m, v) for s, m, v in relevant_stats]
        qual_matches = filter(lambda m: m.comp_level == 'qm', matches)
        playoff_matches = filter(lambda m: m.comp_level != 'qm', matches)
        match_idx = 0
        for level in ['qual', 'playoff']:
            # For benchmarks
            played_matches = 0
            played_matches_75 = 0
            correct_predictions = 0
            correct_predictions_75 = 0
            score_differences = []
            brier_sums = defaultdict(float)
            reset_benchmarks = False

            for match in qual_matches if level == 'qual' else playoff_matches:
                mean_vars = [cc.calculate_before_match(match_idx) for cc in contribution_calculators]
                match_idx += 1
                stat_mean_vars[level] = {}
                for (stat, _, _), mean_var in zip(relevant_stats, mean_vars):
                    stat_mean_vars[level][stat] = copy.deepcopy(mean_var)

                ####################################################################
                # Make prediction
                prediction = cls._predict_match(event, match, stat_mean_vars[level], level=='playoff')
                predictions[level][match.key.id()] = prediction

                # Benchmark prediction
                if match.has_been_played:
                    played_matches += 1
                    if prediction['prob'] > 0.75:
                        played_matches_75 += 1
                    if match.winning_alliance == prediction['winning_alliance']:
                        correct_predictions += 1
                        if prediction['prob'] > 0.75:
                            correct_predictions_75 += 1
                        for alliance_color in ['red', 'blue']:
                            score_differences.append(abs(match.alliances[alliance_color]['score'] - prediction[alliance_color]['score']))
                        brier_sums['score'] += pow(prediction['prob'] - 1, 2)
                    else:
                        brier_sums['score'] += pow(prediction['prob'] - 0, 2)

                    for color in ['red', 'blue']:
                        if event.year == 2016:
                            if match.score_breakdown[color]['teleopDefensesBreached']:
                                brier_sums['breach'] += pow(prediction[color]['prob_breach'] - 1, 2)
                            else:
                                brier_sums['breach'] += pow(prediction[color]['prob_breach'] - 0, 2)
                            if match.score_breakdown[color]['teleopTowerCaptured']:
                                brier_sums['capture'] += pow(prediction[color]['prob_capture'] - 1, 2)
                            else:
                                brier_sums['capture'] += pow(prediction[color]['prob_capture'] - 0, 2)
                        elif event.year == 2017:
                            if match.score_breakdown[color]['kPaRankingPointAchieved']:
                                brier_sums['pressure'] += pow(prediction[color]['prob_pressure'] - 1, 2)
                            else:
                                brier_sums['pressure'] += pow(prediction[color]['prob_pressure'] - 0, 2)
                            if match.score_breakdown[color]['rotorRankingPointAchieved']:
                                brier_sums['gears'] += pow(prediction[color]['prob_gears'] - 1, 2)
                            else:
                                brier_sums['gears'] += pow(prediction[color]['prob_gears'] - 0, 2)

            brier_scores = {}
            for stat, brier_sum in brier_sums.items():
                if stat == 'score':
                    brier_scores['win_loss'] = brier_sum / played_matches
                else:
                    brier_scores[stat] = brier_sum / (2 * played_matches)

            prediction_stats[level] = {
                'wl_accuracy': None if played_matches == 0 else 100 * float(correct_predictions) / played_matches,
                'wl_accuracy_75': None if played_matches_75 == 0 else 100 * float(correct_predictions_75) / played_matches_75,
                'err_mean': np.mean(score_differences) if score_differences else None,
                'err_var': np.var(score_differences) if score_differences else None,
                'brier_scores': brier_scores,
            }

        return predictions, prediction_stats, stat_mean_vars

    @classmethod
    def get_ranking_predictions(cls, matches, match_predictions, n=1000):
        matches = MatchHelper.organizeMatches(matches)['qm']
        if not matches or not match_predictions:
            return None, None

        match_predictions = match_predictions.get('qual')
        if not match_predictions:
            return None, None

        # Calc surrogates
        match_counts = defaultdict(int)
        for match in matches:
            for alliance_color in ['red', 'blue']:
                for team in match.alliances[alliance_color]['teams']:
                    match_counts[team] += 1
        num_matches = min(match_counts.values())
        surrogate_teams = set()
        for k, v in match_counts.items():
            if v > num_matches:
                surrogate_teams.add(k)

        # Calculate ranking points and tiebreakers
        all_rankings = defaultdict(lambda: [0] * n)
        all_ranking_points = defaultdict(lambda: [0] * n)
        last_played_match = None
        for i in xrange(n):
            team_ranking_points = defaultdict(int)
            team_rank_tiebreaker = defaultdict(int)
            num_played = defaultdict(int)
            for match in matches:
                for alliance_color in ['red', 'blue']:
                    for team in match.alliances[alliance_color]['teams']:
                        num_played[team] += 1

                sampled_rp1 = {
                    'red': False,
                    'blue': False,
                }
                sampled_rp2 = {
                    'red': False,
                    'blue': False,
                }
                sampled_tiebreaker = {
                    'red': 0,
                    'blue': 0,
                }
                # Get actual results or sampled results, depending if match has been played
                if match.has_been_played:
                    if not match.score_breakdown:  # Can't do rankings without score breakdown
                        return None, None
                    last_played_match = match.key.id()
                    sampled_winner = match.winning_alliance
                    for alliance_color in ['red', 'blue']:
                        if match.year == 2016:
                            sampled_rp1[alliance_color] = match.score_breakdown[alliance_color]['teleopDefensesBreached']
                            sampled_rp2[alliance_color] = match.score_breakdown[alliance_color]['teleopTowerCaptured']
                            sampled_tiebreaker[alliance_color] = match.score_breakdown[alliance_color]['autoPoints']
                        elif match.year == 2017:
                            sampled_rp1[alliance_color] = match.score_breakdown[alliance_color]['kPaRankingPointAchieved']
                            sampled_rp2[alliance_color] = match.score_breakdown[alliance_color]['rotorRankingPointAchieved']
                            sampled_tiebreaker[alliance_color] = match.score_breakdown[alliance_color]['totalPoints']
                        elif match.year == 2018:
                            sampled_rp1[alliance_color] = match.score_breakdown[alliance_color]['autoQuestRankingPoint']
                            sampled_rp2[alliance_color] = match.score_breakdown[alliance_color]['faceTheBossRankingPoint']
                            sampled_tiebreaker[alliance_color] = match.score_breakdown[alliance_color]['totalPoints']
                        elif match.year == 2019:
                            sampled_rp1[alliance_color] = match.score_breakdown[alliance_color]['completeRocketRankingPoint']
                            sampled_rp2[alliance_color] = match.score_breakdown[alliance_color]['habDockingRankingPoint']
                            sampled_tiebreaker[alliance_color] = match.score_breakdown[alliance_color]['totalPoints']
                        elif match.year == 2020:
                            sampled_rp1[alliance_color] = match.score_breakdown[alliance_color]['shieldEnergizedRankingPoint']
                            sampled_rp2[alliance_color] = match.score_breakdown[alliance_color]['shieldOperationalRankingPoint']
                            sampled_tiebreaker[alliance_color] = match.score_breakdown[alliance_color]['totalPoints']
                else:
                    prediction = match_predictions[match.key.id()]
                    if np.random.uniform(high=1) < prediction['prob']:
                        sampled_winner = prediction['winning_alliance']
                    else:
                        if prediction['winning_alliance'] == 'red':
                            sampled_winner = 'blue'
                        elif prediction['winning_alliance'] == 'blue':
                            sampled_winner = 'red'

                    for alliance_color in ['red', 'blue']:
                        if match.year == 2016:
                            sampled_rp1[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_breach']
                            sampled_rp2[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_capture']
                            sampled_tiebreaker[alliance_color] = prediction[alliance_color]['auto_points']
                        elif match.year == 2017:
                            sampled_rp1[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_pressure']
                            sampled_rp2[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_gears']
                            sampled_tiebreaker[alliance_color] = prediction[alliance_color]['score']
                        elif match.year == 2018:
                            sampled_rp1[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_auto_quest']
                            sampled_rp2[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_face_boss']
                            sampled_tiebreaker[alliance_color] = prediction[alliance_color]['score']
                        elif match.year == 2019:
                            sampled_rp1[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_complete_rocket']
                            sampled_rp2[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_hab_docking']
                            sampled_tiebreaker[alliance_color] = prediction[alliance_color]['score']
                        elif match.year == 2020:
                            sampled_rp1[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_shield_energized']
                            sampled_rp2[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_shield_operational']
                            sampled_tiebreaker[alliance_color] = prediction[alliance_color]['score']

                # Using match results, update RP and tiebreaker
                for alliance_color in ['red', 'blue']:
                    for team in match.alliances[alliance_color]['teams']:
                        if team in surrogate_teams and num_played[team] == 3:
                            continue
                        if sampled_rp1[alliance_color]:
                            team_ranking_points[team] += 1
                        if sampled_rp2[alliance_color]:
                            team_ranking_points[team] += 1
                        team_rank_tiebreaker[team] += sampled_tiebreaker[alliance_color]

                if sampled_winner == '':
                    for alliance_color in ['red', 'blue']:
                        for team in match.alliances[alliance_color]['teams']:
                            if team in surrogate_teams and num_played[team] == 3:
                                continue
                            team_ranking_points[team] += 1
                else:
                    for team in match.alliances[sampled_winner]['teams']:
                        if team in surrogate_teams and num_played[team] == 3:
                            continue
                        team_ranking_points[team] += 2

                    sampled_loser = 'red' if sampled_winner == 'blue' else 'blue'
                    for team in match.alliances[sampled_loser]['teams']:
                        team_ranking_points[team] += 0

            # Compute ranks for this sample
            sample_rankings = sorted(team_ranking_points.items(), key=lambda x: -team_rank_tiebreaker[x[0]])  # Sort by tiebreaker.
            sample_rankings = sorted(sample_rankings, key=lambda x: -x[1])  # Sort by RP. Sort is stable.
            for rank, (team, ranking_points) in enumerate(sample_rankings):
                all_rankings[team][i] = rank + 1
                all_ranking_points[team][i] = ranking_points

        rankings = {}
        for team, team_rankings in all_rankings.items():
            avg_rank = np.mean(team_rankings)
            min_rank = min(team_rankings)
            median_rank = np.median(team_rankings)
            max_rank = max(team_rankings)
            avg_rp = np.mean(all_ranking_points[team])
            min_rp = min(all_ranking_points[team])
            max_rp = max(all_ranking_points[team])

            rankings[team] = (avg_rank, min_rank, median_rank, max_rank, avg_rp, min_rp, max_rp)

        ranking_predictions = sorted(rankings.items(), key=lambda x: x[1][0])  # Sort by avg_rank

        ranking_stats = {'last_played_match': last_played_match}

        return ranking_predictions, ranking_stats
