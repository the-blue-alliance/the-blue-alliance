from collections import defaultdict
import math
import numpy as np

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
                    boulders = match.score_breakdown[alliance_color]['autoBouldersLow'] + \
                        match.score_breakdown[alliance_color]['autoBouldersHigh'] + \
                        match.score_breakdown[alliance_color]['teleopBouldersLow'] + \
                        match.score_breakdown[alliance_color]['teleopBouldersHigh']
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
    def _predict_match(cls, match, ixoprs, ixoprs_boulder):
        score_var = 50**2  # TODO temporary set variance to be huge
        boulder_var = 8**2  # TODO get real value

        red_score = 0
        red_boulders = 0
        for team in match.alliances['red']['teams']:
            red_score += ixoprs[team[3:]]
            red_boulders += ixoprs_boulder[team[3:]]
        blue_score = 0
        blue_boulders = 0
        for team in match.alliances['blue']['teams']:
            blue_score += ixoprs[team[3:]]
            blue_boulders += ixoprs_boulder[team[3:]]

        # Prob win
        mu = abs(red_score - blue_score)
        var = 2 * score_var
        prob = 1 - cls._normcdf(-mu / np.sqrt(var))
        if math.isnan(prob):
            prob = 0.5

        # Prob capture
        mu = red_boulders - 8
        red_prob_capture = 1 - cls._normcdf(-mu / np.sqrt(boulder_var))

        mu = blue_boulders - 8
        blue_prob_capture = 1 - cls._normcdf(-mu / np.sqrt(boulder_var))

        if red_score > blue_score:
            winning_alliance = 'red'
        elif blue_score > red_score:
            winning_alliance = 'blue'
        else:
            winning_alliance = ''

        # Prob breach
        #TODO
        red_prob_breach = 0.7
        blue_prob_breach = 0.7

        prediction = {
            'red': {'score': red_score, 'boulders': red_boulders, 'prob_capture': red_prob_capture * 100, 'prob_breach': red_prob_breach * 100},
            'blue': {'score': blue_score, 'boulders': blue_boulders, 'prob_capture': blue_prob_capture * 100, 'prob_breach': blue_prob_breach * 100},
            'winning_alliance': winning_alliance,
            'prob': prob * 100,
        }
        return prediction

    @classmethod
    def get_match_predictions(cls, matches):
        if not matches:
            return None, None

        # Build team_list
        team_list = set()
        for match in matches:
            alliances = match.alliances
            for alliance_color in ['red', 'blue']:
                for team in alliances[alliance_color]['teams']:
                    team_list.add(team[3:])  # turns "frc254B" into "254B"
        team_list = list(team_list)

        # Build team_id_map
        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        # Calculate ixOPR after each played match
        n = len(team_list)
        M = np.zeros([n, n])
        s = np.zeros([n, 1])
        s_boulder = np.zeros([n, 1])

        # Construct M and populate s with initial guess using previous event OPRs
        last_event_oprs = MatchstatsHelper.get_last_event_oprs(team_list, matches[0].event)
        last_event_oprs_boulder = dict()  # TODO: Initialize with previous event
        init_opr = np.mean(last_event_oprs.values())  # Initialize with average OPR
        # init_opr_boulder = np.mean(last_event_oprs_boulder.values())  # TODO Initialize with average boulder OPR
        init_opr_boulder = 1  # TODO temp. Replace with above
        for match in matches:
            for alliance_color in ['red', 'blue']:
                for team1 in match.alliances[alliance_color]['teams']:
                    team1_id = team_id_map[team1[3:]]
                    for team2 in match.alliances[alliance_color]['teams']:
                        M[team1_id, team_id_map[team2[3:]]] += 1
                    s[team1_id] += last_event_oprs.get(team1[3:], init_opr)
                    s_boulder[team1_id] += last_event_oprs_boulder.get(team1[3:], init_opr_boulder)

        # Calculate ixOPR and make predictions before match has been played then update s
        predictions = {}
        correct_predictions = 0
        played_matches = 0
        correct_predictions_75 = 0
        played_matches_75 = 0
        score_differences = []
        played_match_keys = set()
        all_scores_sum = 0
        all_boulders_sum = 0
        for i, match in enumerate(matches):
            # Solving M*x = s for x
            x = np.dot(np.linalg.pinv(M), s)
            x_boulder = np.dot(np.linalg.pinv(M), s_boulder)
            ixoprs = {}
            ixoprs_boulder = {}
            for team, opr, opr_boulder in zip(team_list, x, x_boulder):
                ixoprs[team] = opr[0]
                ixoprs_boulder[team] = opr_boulder[0]

            # Do 2 iterations of ixOPR
            for _ in range(2):
                s2, s2_boulder = cls._build_s_matrix(matches, team_id_map, n, ixoprs, ixoprs_boulder, played_match_keys)
                x = np.dot(np.linalg.pinv(M), s2)
                x_boulder = np.dot(np.linalg.pinv(M), s2_boulder)
                ixoprs = {}
                ixoprs_boulder = {}
                for team, opr, opr_boulder in zip(team_list, x, x_boulder):
                    ixoprs[team] = opr[0]
                    ixoprs_boulder[team] = opr_boulder[0]

            # Make and benchmark predictions
            prediction = cls._predict_match(match, ixoprs, ixoprs_boulder)
            predictions[match.key.id()] = prediction
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

            # Done with this match
            played_match_keys.add(match.key.id())

            # Update s
            for alliance_color in ['red', 'blue']:
                all_scores_sum += match.alliances[alliance_color]['score']
                all_boulders_sum += match.score_breakdown[alliance_color]['autoBouldersLow'] + \
                    match.score_breakdown[alliance_color]['autoBouldersHigh'] + \
                    match.score_breakdown[alliance_color]['teleopBouldersLow'] + \
                    match.score_breakdown[alliance_color]['teleopBouldersHigh']
            init_opr = float(all_scores_sum) / (i + 1) / 6  # Initialize with 1/3 of average scores (2 alliances per match)
            init_boulders = float(all_boulders_sum) / (i + 1) / 6
            s, s_boulder = cls._build_s_matrix(matches, team_id_map, n, last_event_oprs, last_event_oprs_boulder, played_match_keys, init_opr=init_opr, init_boulders=init_boulders)

        prediction_stats = {
            'wl_accuracy': None if played_matches == 0 else 100 * float(correct_predictions) / played_matches,
            'wl_accuracy_75': None if played_matches_75 == 0 else 100 * float(correct_predictions_75) / played_matches_75,
            'err_mean': np.mean(score_differences),
            'err_var': np.var(score_differences),
        }

        return predictions, prediction_stats

    @classmethod
    def get_ranking_predictions(cls, matches, match_predictions, n=100):
        """
        Only works for 2016
        """
        if not matches:
            return None, None

        team_qual_points = defaultdict(lambda: [0] * n)
        for i in xrange(n):
            for match in matches:
                if match.has_been_played and False:  # TODO temp for testing
                    sampled_winner = match.winning_alliance
                else:
                    prediction = match_predictions[match.key.id()]
                    if np.random.uniform(high=100) < prediction['prob']:
                        sampled_winner = prediction['winning_alliance']
                    else:
                        if prediction['winning_alliance'] == 'red':
                            sampled_winner = 'blue'
                        elif prediction['winning_alliance'] == 'blue':
                            sampled_winner = 'red'

                if sampled_winner == '':
                    for alliance_color in ['red', 'blue']:
                        for team in match.alliances[alliance_color]['teams']:
                            team_qual_points[team][i] += 1
                else:
                    for team in match.alliances[sampled_winner]['teams']:
                        team_qual_points[team][i] += 2

        # for team, qual_points in sorted(team_qual_points.items(), key=lambda x: int(x[0][3:])):
        #     print team, np.mean(qual_points)

        # print team_qual_points['frc254']

        return None, None
