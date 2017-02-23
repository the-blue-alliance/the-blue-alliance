from collections import defaultdict
import math
import numpy as np
import time

from consts.event_type import EventType
from helpers.matchstats_helper import MatchstatsHelper


class ContributionCalculator(object):
    def __init__(self, matches, stat, default_mean, default_var):
        """
        stat: 'score' or a specific breakdown like '2016autoPoints'
        """
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
            if match.comp_level != 'qm':  # only consider quals matches
                continue
            for alliance_color in ['red', 'blue']:
                for team in match.alliances[alliance_color]['teams']:
                    team_list.add(team)

        team_list = list(team_list)
        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        return team_list, team_id_map

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
        all_team_means = {}  # TODO
        for team in self._team_list:
            mean = self._default_mean
            if team not in all_team_means:
                if all_team_means:
                    mean = np.mean([ato[-1] for ato in all_team_means.values()])
                elif self._mean_sums:
                    mean = np.mean(self._mean_sums) / 3
            else:
                weight_sum = 0
                for j, o in enumerate(reversed(all_team_means[team])):
                    weight = pow(0.1, j)
                    opr += weight * o
                    weight_sum += weight
                mean /= weight_sum

            self._Oe[self._team_id_map[team]] = mean
            self._diags[self._team_id_map[team]] = 3  # TODO

        # MMSE Contribution Mean
        Omean = np.linalg.inv(Aoo + np.diag(self._diags)).dot(AoT.dot(self._Mmean) + np.diag(self._diags).dot(self._Oe))
        for team, Omean in zip(self._team_list, Omean):
            self._means[team] = Omean[0]

        ####################################################################
        # Estimate Team Variances
        # Populate priors
        all_team_vars = {}  # TODO
        for team in self._team_list:
            var = self._default_var
            if team not in all_team_vars:
                if all_team_vars:
                    var = np.mean([ato[-1] for ato in all_team_vars.values()])
                elif self._var_sums:
                    var = np.mean(self._var_sums) / 3
            else:
                var = 0
                weight_sum = 0
                for j, o in enumerate(reversed(all_team_vars[team])):
                    weight = pow(0.1, j)
                    var += weight * o
                    weight_sum += weight
                var /= weight_sum

            self._Oe[self._team_id_map[team]] = var
            self._diags[self._team_id_map[team]] = 3  # TODO

        # MMSE Contribution Variance
        Ovar = abs(np.linalg.inv(Aoo + np.diag(self._diags)).dot(AoT.dot(self._Mvar) + np.diag(self._diags).dot(self._Oe)))
        for team, stat in zip(self._team_list, Ovar):
            self._vars[team] = stat[0]

        ####################################################################
        # Add results for next iter
        match = self._matches[i]
        if match.has_been_played:
            means = {}
            for color in ['red', 'blue']:
                if self._stat == 'score':
                    means[color] = match.alliances[color]['score']
                elif self._stat == '2016autoPointsOPR':
                    means[color] = match.score_breakdown[color]['autoPoints']
                elif self._stat == '2016bouldersOPR':
                    means[color] = (
                        match.score_breakdown[color].get('autoBouldersLow', 0) +
                        match.score_breakdown[color].get('autoBouldersHigh', 0) +
                        match.score_breakdown[color].get('teleopBouldersLow', 0) +
                        match.score_breakdown[color].get('teleopBouldersHigh', 0))
                elif self._stat == '2016crossingsOPR':
                    means[color] = (
                        match.score_breakdown[color].get('position1crossings', 0) +
                        match.score_breakdown[color].get('position2crossings', 0) +
                        match.score_breakdown[color].get('position3crossings', 0) +
                        match.score_breakdown[color].get('position4crossings', 0) +
                        match.score_breakdown[color].get('position5crossings', 0))
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

        return self._means, self._vars


class PredictionHelper(object):
    """
    Only works for 2016
    """
    @classmethod
    def _normcdf(cls, x):
        return (1.0 + math.erf(x / np.sqrt(2.0))) / 2.0

    @classmethod
    def _predict_match(cls, match, stat_mean_vars, tower_strength):
        # score_var = 40**2  # TODO temporary set variance to be huge
        # boulder_var = 5**2  # TODO get real value
        # crossing_var = 4**2  # TODO get real value

        red_score = 0
        red_score_var = 0
        red_auto_points = 0  # Used for tiebreaking
        red_boulders = 0
        red_boulders_var = 0
        red_num_crossings = 0
        red_num_crossings_var = 0
        for team in match.alliances['red']['teams']:
            red_score += stat_mean_vars['score'][0][team]
            red_score_var += stat_mean_vars['score'][1][team]

            red_auto_points += stat_mean_vars['2016autoPointsOPR'][0][team]

            red_boulders += stat_mean_vars['2016bouldersOPR'][0][team]
            red_boulders_var += stat_mean_vars['2016bouldersOPR'][1][team]

            # Crossing OPR usually underestimates. hacky fix to make numbers more believable
            red_num_crossings += max(0, stat_mean_vars['2016crossingsOPR'][0][team]) * 1.2
            red_num_crossings_var += stat_mean_vars['2016crossingsOPR'][1][team]

        blue_score = 0
        blue_score_var = 0
        blue_auto_points = 0  # Used for tiebreaking
        blue_boulders = 0
        blue_boulders_var = 0
        blue_num_crossings = 0
        blue_num_crossings_var = 0
        for team in match.alliances['blue']['teams']:
            blue_score += stat_mean_vars['score'][0][team]
            blue_score_var += stat_mean_vars['score'][1][team]

            blue_auto_points += stat_mean_vars['2016autoPointsOPR'][0][team]

            blue_boulders += stat_mean_vars['2016bouldersOPR'][0][team]
            blue_boulders_var += stat_mean_vars['2016bouldersOPR'][1][team]

            # Crossing OPR usually underestimates. hacky fix to make numbers more believable
            blue_num_crossings += max(0, stat_mean_vars['2016crossingsOPR'][0][team]) * 1.2
            blue_num_crossings_var += stat_mean_vars['2016crossingsOPR'][1][team]

        # Prob win
        mu = abs(red_score - blue_score)
        prob = 1 - cls._normcdf(-mu / np.sqrt(red_score_var + blue_score_var))
        if math.isnan(prob):
            prob = 0.5

        # Prob capture
        mu = red_boulders - tower_strength
        red_prob_capture = 1 - cls._normcdf(-mu / np.sqrt(red_boulders_var))

        mu = blue_boulders - tower_strength
        blue_prob_capture = 1 - cls._normcdf(-mu / np.sqrt(blue_boulders_var))

        if red_score > blue_score:
            winning_alliance = 'red'
        elif blue_score > red_score:
            winning_alliance = 'blue'
        else:
            winning_alliance = ''

        # Prob breach
        crossings_to_breach = 8
        mu = red_num_crossings - crossings_to_breach
        red_prob_breach = 1 - cls._normcdf(-mu / np.sqrt(red_num_crossings_var))

        mu = blue_num_crossings - crossings_to_breach
        blue_prob_breach = 1 - cls._normcdf(-mu / np.sqrt(blue_num_crossings_var))

        prediction = {
            'red': {
                'score': red_score,
                'auto_points': red_auto_points,
                'boulders': red_boulders,
                'prob_capture': red_prob_capture,
                'prob_breach': red_prob_breach
            },
            'blue': {
                'score': blue_score,
                'auto_points': blue_auto_points,
                'boulders': blue_boulders,
                'prob_capture': blue_prob_capture,
                'prob_breach': blue_prob_breach
            },
            'winning_alliance': winning_alliance,
            'prob': prob,
        }
        return prediction

    @classmethod
    def get_match_predictions(cls, matches):
        if not matches:
            return None, None

        event_key = matches[0].event
        event = event_key.get()

        # # Setup
        # team_list, team_id_map = cls._build_team_mapping(matches)
        # # last_event_stats = MatchstatsHelper.get_last_event_stats(team_list, event_key)

        # # Setup matrices
        # m = len(matches)
        # t = len(team_list)
        # Ar = np.zeros((m, t))
        # Ab = np.zeros((m, t))
        # Mr_mean = np.zeros((m, 1))
        # Mb_mean = np.zeros((m, 1))
        # Mr_var = np.zeros((m, 1))
        # Mb_var = np.zeros((m, 1))

        # init_stats_sums = defaultdict(int)
        # init_stats_totals = defaultdict(int)
        # for _, stats in last_event_stats.items():
        #     for stat, stat_value in stats.items():
        #         init_stats_sums[stat] += stat_value
        #         init_stats_totals[stat] += 1

        # init_stats_default = defaultdict(int)
        # for stat, stat_sum in init_stats_sums.items():
        #     init_stats_default[stat] = float(stat_sum) / init_stats_totals[stat]

        # relevant_stats = [
        #     'oprs',
        #     '2016autoPointsOPR',
        #     '2016crossingsOPR',
        #     '2016bouldersOPR'
        # ]

        # Make predictions before each match
        predictions = {}
        played_matches = 0
        played_matches_75 = 0
        correct_predictions = 0
        correct_predictions_75 = 0
        score_differences = []
        stats_sum = defaultdict(int)
        brier_sum = 0
        scores = []
        var_sums = []
        team_oprs = {}
        team_vars = {}
        all_team_oprs = {}  # TODO
        all_team_vars = {}  # TODO

        relevant_stats = [('score', 20, 10**2)]
        # TODO: populate based on year
        relevant_stats += [
            ('2016autoPointsOPR', 20, 10**2),
            ('2016crossingsOPR', 0, 1**2),
            ('2016bouldersOPR', 0, 1**2),
        ]
        contribution_calculators = [ContributionCalculator(matches, s, m, v) for s, m, v in relevant_stats]
        for i, match in enumerate(matches):
            mean_vars = [cc.calculate_before_match(i) for cc in contribution_calculators]
            stat_mean_vars = {}
            for (stat, _, _), mean_var in zip(relevant_stats, mean_vars):
                stat_mean_vars[stat] = mean_var

            ####################################################################
            # Make prediction
            tower_strength = 10 if (event.event_type_enum in EventType.CMP_EVENT_TYPES or event.key.id() == '2016cc') else 8
            prediction = cls._predict_match(match, stat_mean_vars, tower_strength)
            predictions[match.key.id()] = prediction

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
                    brier_sum += pow(prediction['prob'] - 1, 2)
                else:
                    brier_sum += pow(prediction['prob'] - 0, 2)

            # # Update init_stats
            # if match.has_been_played and match.score_breakdown:
            #     for alliance_color in ['red', 'blue']:
            #         stats_sum['score'] += match.alliances[alliance_color]['score']

            #         for stat in relevant_stats:
            #             if stat == '2016autoPointsOPR':
            #                 init_stats_default[stat] += match.score_breakdown[alliance_color]['autoPoints']
            #             elif stat == '2016bouldersOPR':
            #                 init_stats_default[stat] += (
            #                     match.score_breakdown[alliance_color].get('autoBouldersLow', 0) +
            #                     match.score_breakdown[alliance_color].get('autoBouldersHigh', 0) +
            #                     match.score_breakdown[alliance_color].get('teleopBouldersLow', 0) +
            #                     match.score_breakdown[alliance_color].get('teleopBouldersHigh', 0))
            #             elif stat == '2016crossingsOPR':
            #                 init_stats_default[stat] += (
            #                     match.score_breakdown[alliance_color].get('position1crossings', 0) +
            #                     match.score_breakdown[alliance_color].get('position2crossings', 0) +
            #                     match.score_breakdown[alliance_color].get('position3crossings', 0) +
            #                     match.score_breakdown[alliance_color].get('position4crossings', 0) +
            #                     match.score_breakdown[alliance_color].get('position5crossings', 0))

            # init_stats_default['oprs'] = float(stats_sum['score']) / (i + 1) / 6  # Initialize with 1/3 of average scores (2 alliances per match)
            # for stat in relevant_stats:
            #     if stat != 'oprs':
            #         init_stats_default[stat] = float(stats_sum[stat]) / (i + 1) / 6  # Initialize with 1/3 of average scores (2 alliances per match)

        prediction_stats = {
            'wl_accuracy': None if played_matches == 0 else 100 * float(correct_predictions) / played_matches,
            'wl_accuracy_75': None if played_matches_75 == 0 else 100 * float(correct_predictions_75) / played_matches_75,
            'err_mean': np.mean(score_differences) if score_differences else None,
            'err_var': np.var(score_differences) if score_differences else None,
            'brier_score': brier_sum / played_matches,
        }

        return predictions, prediction_stats

    @classmethod
    def get_ranking_predictions(cls, matches, match_predictions, n=1000):
        """
        Only works for 2016
        """
        if not matches:
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

                sampled_breach = {}
                sampled_capture = {}
                sampled_tiebreaker = {}
                # Get actual results or sampled results, depending if match has been played
                if match.has_been_played:
                    if not match.score_breakdown:  # Can't do rankings without score breakdown
                        return None, None
                    last_played_match = match.key.id()
                    sampled_winner = match.winning_alliance
                    for alliance_color in ['red', 'blue']:
                        sampled_breach[alliance_color] = match.score_breakdown[alliance_color]['teleopDefensesBreached']
                        sampled_capture[alliance_color] = match.score_breakdown[alliance_color]['teleopTowerCaptured']
                        sampled_tiebreaker[alliance_color] = match.score_breakdown[alliance_color]['autoPoints']
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
                        sampled_breach[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_breach']
                        sampled_capture[alliance_color] = np.random.uniform(high=1) < prediction[alliance_color]['prob_capture']
                        sampled_tiebreaker[alliance_color] = prediction[alliance_color]['auto_points']

                # Using match results, update RP and tiebreaker
                for alliance_color in ['red', 'blue']:
                    for team in match.alliances[alliance_color]['teams']:
                        if team in surrogate_teams and num_played[team] == 3:
                            continue
                        if sampled_breach[alliance_color]:
                            team_ranking_points[team] += 1
                        if sampled_capture[alliance_color]:
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
