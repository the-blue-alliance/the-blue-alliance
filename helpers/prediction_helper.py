from collections import defaultdict
import math
import numpy as np
import time

from consts.event_type import EventType
from helpers.matchstats_helper import MatchstatsHelper


class PredictionHelper(object):
    """
    Only works for 2016
    """
    @classmethod
    def _normcdf(cls, x):
        return (1.0 + math.erf(x / np.sqrt(2.0))) / 2.0

    @classmethod
    def _build_s_matrix(cls, matches, team_id_map, n, init_oprs, init_oprs_boulder, played_match_keys, init_opr=0, init_boulders=0):
        s = np.zeros([n, 1])
        s_boulder = np.zeros([n, 1])
        for match in matches:
            for alliance_color in ['red', 'blue']:
                if match.has_been_played and match.key.id() in played_match_keys:
                    score = match.alliances[alliance_color]['score']
                    boulders = match.score_breakdown[alliance_color]['2016bouldersOPR']
                else:
                    score = 0
                    boulders = 0
                    for team in match.alliances[alliance_color]['teams']:
                        team = team[3:]  # turns "frc254B" into "254B"
                        score += init_oprs.get(team, init_opr)
                        boulders += init_oprs_boulder.get(team, init_boulders)

                for team in match.alliances[alliance_color]['teams']:
                    team_id = team_id_map[team[3:]]
                    s[team_id] += score
                    s_boulder[team_id] += boulders

        return s, s_boulder

    @classmethod
    def _predict_match(cls, match, all_stats, is_champs):
        score_var = 40**2  # TODO temporary set variance to be huge
        boulder_var = 5**2  # TODO get real value
        crossing_var = 4**2  # TODO get real value

        red_score = 0
        red_auto_points = 0  # Used for tiebreaking
        red_boulders = 0
        red_num_crossings = 0
        for team in match.alliances['red']['teams']:
            red_score += all_stats['oprs'][team[3:]]
            red_auto_points += all_stats['2016autoPointsOPR'][team[3:]]
            red_boulders += all_stats['2016bouldersOPR'][team[3:]]
            # Crossing OPR usually underestimates. hacky fix to make numbers more believable
            red_num_crossings += max(0, all_stats['2016crossingsOPR'][team[3:]]) * 1.2

        blue_score = 0
        blue_auto_points = 0  # Used for tiebreaking
        blue_boulders = 0
        blue_num_crossings = 0
        for team in match.alliances['blue']['teams']:
            blue_score += all_stats['oprs'][team[3:]]
            blue_auto_points += all_stats['2016autoPointsOPR'][team[3:]]
            blue_boulders += all_stats['2016bouldersOPR'][team[3:]]
            # Crossing OPR usually underestimates. hacky fix to make numbers more believable
            blue_num_crossings += max(0, all_stats['2016crossingsOPR'][team[3:]]) * 1.2

        # Prob win
        mu = abs(red_score - blue_score)
        var = 2 * score_var
        prob = 1 - cls._normcdf(-mu / np.sqrt(var))
        if math.isnan(prob):
            prob = 0.5

        # Prob capture
        tower_strength = 10 if is_champs else 8
        mu = red_boulders - tower_strength
        red_prob_capture = 1 - cls._normcdf(-mu / np.sqrt(boulder_var))

        mu = blue_boulders - tower_strength
        blue_prob_capture = 1 - cls._normcdf(-mu / np.sqrt(boulder_var))

        if red_score > blue_score:
            winning_alliance = 'red'
        elif blue_score > red_score:
            winning_alliance = 'blue'
        else:
            winning_alliance = ''

        # Prob breach
        crossings_to_breach = 8
        mu = red_num_crossings - crossings_to_breach
        red_prob_breach = 1 - cls._normcdf(-mu / np.sqrt(crossing_var))

        mu = blue_num_crossings - crossings_to_breach
        blue_prob_breach = 1 - cls._normcdf(-mu / np.sqrt(crossing_var))

        # Artificially limit prob breach range
        red_prob_breach = min(max(red_prob_breach, 0.1), 0.95)
        blue_prob_breach = min(max(blue_prob_breach, 0.1), 0.95)

        prediction = {
            'red': {
                'score': red_score,
                'auto_points': red_auto_points,
                'boulders': red_boulders,
                'prob_capture': red_prob_capture * 100,
                'prob_breach': red_prob_breach * 100
            },
            'blue': {
                'score': blue_score,
                'auto_points': blue_auto_points,
                'boulders': blue_boulders,
                'prob_capture': blue_prob_capture * 100,
                'prob_breach': blue_prob_breach * 100
            },
            'winning_alliance': winning_alliance,
            'prob': prob * 100,
        }
        return prediction

    @classmethod
    def get_match_predictions(cls, matches):
        if not matches:
            return None, None

        event_key = matches[0].event
        event = event_key.get()

        # Setup
        team_list, team_id_map = MatchstatsHelper.build_team_mapping(matches)
        last_event_stats = MatchstatsHelper.get_last_event_stats(team_list, event_key)
        Minv = MatchstatsHelper.build_Minv_matrix(matches, team_id_map)

        init_stats_sums = defaultdict(int)
        init_stats_totals = defaultdict(int)
        for _, stats in last_event_stats.items():
            for stat, stat_value in stats.items():
                init_stats_sums[stat] += stat_value
                init_stats_totals[stat] += 1

        init_stats_default = defaultdict(int)
        for stat, stat_sum in init_stats_sums.items():
            init_stats_default[stat] = float(stat_sum) / init_stats_totals[stat]

        relevant_stats = [
            'oprs',
            '2016autoPointsOPR',
            '2016crossingsOPR',
            '2016bouldersOPR'
        ]

        # Make predictions before each match
        predictions = {}
        played_matches = 0
        played_matches_75 = 0
        correct_predictions = 0
        correct_predictions_75 = 0
        score_differences = []
        stats_sum = defaultdict(int)
        for i, match in enumerate(matches):
            # Calculate ixOPR
            all_ixoprs = {}
            for stat in relevant_stats:
                all_ixoprs[stat] = MatchstatsHelper.calc_stat(
                    matches, team_list, team_id_map, Minv, stat,
                    init_stats=last_event_stats,
                    init_stats_default=init_stats_default[stat],
                    limit_matches=i)
            for _ in xrange(2):
                for stat in relevant_stats:
                    start = time.time()
                    all_ixoprs[stat] = MatchstatsHelper.calc_stat(
                        matches, team_list, team_id_map, Minv, stat,
                        init_stats=all_ixoprs,
                        init_stats_default=init_stats_default[stat],
                        limit_matches=i)

            # Make prediction
            is_champs = event.event_type_enum in EventType.CMP_EVENT_TYPES
            prediction = cls._predict_match(match, all_ixoprs, is_champs)
            predictions[match.key.id()] = prediction

            # Benchmark prediction
            if match.has_been_played:
                played_matches += 1
                if prediction['prob'] > 75:
                    played_matches_75 += 1
                if match.winning_alliance == prediction['winning_alliance']:
                    correct_predictions += 1
                    if prediction['prob'] > 75:
                        correct_predictions_75 += 1
                    for alliance_color in ['red', 'blue']:
                        score_differences.append(abs(match.alliances[alliance_color]['score'] - prediction[alliance_color]['score']))

            # Update init_stats
            if match.has_been_played and match.score_breakdown:
                for alliance_color in ['red', 'blue']:
                    stats_sum['score'] += match.alliances[alliance_color]['score']

                    for stat in relevant_stats:
                        if stat == '2016autoPointsOPR':
                            init_stats_default[stat] += match.score_breakdown[alliance_color]['autoPoints']
                        elif stat == '2016bouldersOPR':
                            init_stats_default[stat] += (
                                match.score_breakdown[alliance_color]['autoBouldersLow'] +
                                match.score_breakdown[alliance_color]['autoBouldersHigh'] +
                                match.score_breakdown[alliance_color]['teleopBouldersLow'] +
                                match.score_breakdown[alliance_color]['teleopBouldersHigh'])
                        elif stat == '2016crossingsOPR':
                            init_stats_default[stat] += (
                                match.score_breakdown[alliance_color]['position1crossings'] +
                                match.score_breakdown[alliance_color]['position2crossings'] +
                                match.score_breakdown[alliance_color]['position3crossings'] +
                                match.score_breakdown[alliance_color]['position4crossings'] +
                                match.score_breakdown[alliance_color]['position5crossings'])

            init_stats_default['oprs'] = float(stats_sum['score']) / (i + 1) / 6  # Initialize with 1/3 of average scores (2 alliances per match)
            for stat in relevant_stats:
                if stat != 'oprs':
                    init_stats_default[stat] = float(stats_sum[stat]) / (i + 1) / 6  # Initialize with 1/3 of average scores (2 alliances per match)

        prediction_stats = {
            'wl_accuracy': None if played_matches == 0 else 100 * float(correct_predictions) / played_matches,
            'wl_accuracy_75': None if played_matches_75 == 0 else 100 * float(correct_predictions_75) / played_matches_75,
            'err_mean': np.mean(score_differences) if score_differences else None,
            'err_var': np.var(score_differences) if score_differences else None,
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
                if not match.score_breakdown:  # Can't do rankings without score breakdown
                    return None, None

                for alliance_color in ['red', 'blue']:
                    for team in match.alliances[alliance_color]['teams']:
                        num_played[team] += 1

                sampled_breach = {}
                sampled_capture = {}
                sampled_tiebreaker = {}
                # Get actual results or sampled results, depending if match has been played
                if match.has_been_played:
                    last_played_match = match.key.id()
                    sampled_winner = match.winning_alliance
                    for alliance_color in ['red', 'blue']:
                        sampled_breach[alliance_color] = match.score_breakdown[alliance_color]['teleopDefensesBreached']
                        sampled_capture[alliance_color] = match.score_breakdown[alliance_color]['teleopTowerCaptured']
                        sampled_tiebreaker[alliance_color] = match.score_breakdown[alliance_color]['autoPoints']
                else:
                    prediction = match_predictions[match.key.id()]
                    if np.random.uniform(high=100) < prediction['prob']:
                        sampled_winner = prediction['winning_alliance']
                    else:
                        if prediction['winning_alliance'] == 'red':
                            sampled_winner = 'blue'
                        elif prediction['winning_alliance'] == 'blue':
                            sampled_winner = 'red'

                    for alliance_color in ['red', 'blue']:
                        sampled_breach[alliance_color] = np.random.uniform(high=100) < prediction[alliance_color]['prob_breach']
                        sampled_capture[alliance_color] = np.random.uniform(high=100) < prediction[alliance_color]['prob_capture']
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
