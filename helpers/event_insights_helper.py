import logging
from collections import defaultdict


class EventInsightsHelper(object):
    @classmethod
    def calculate_event_insights(cls, matches, year):
        INSIGHTS_MAP = {
            2016: cls.calculate_event_insights_2016
        }

        if year in INSIGHTS_MAP:
            return INSIGHTS_MAP[year](matches)
        else:
            return None

    @classmethod
    def calculate_event_insights_2016(cls, matches):
        qual_matches = []
        playoff_matches = []
        for match in matches:
            if match.comp_level == 'qm':
                qual_matches.append(match)
            else:
                playoff_matches.append(match)

        qual_insights = cls._calculate_event_insights_2016_helper(qual_matches)
        playoff_insights = cls._calculate_event_insights_2016_helper(playoff_matches)

        return {
            'qual': qual_insights,
            'playoff': playoff_insights,
        }

    @classmethod
    def _calculate_event_insights_2016_helper(cls, matches):
        # defenses
        defense_opportunities = defaultdict(int)
        defense_damaged = defaultdict(int)
        breaches = 0

        # towers
        high_goals = 0
        low_goals = 0
        challenges = 0
        scales = 0
        captures = 0

        # scores
        winning_scores = 0
        win_margins = 0
        total_scores = 0
        auto_scores = 0
        crossing_scores = 0
        boulder_scores = 0
        tower_scores = 0
        foul_scores = 0
        high_score = [0, "", ""]  # score, match key, match name

        finished_matches = 0
        has_insights = False
        for match in matches:
            if not match.has_been_played:
                continue

            red_score = match.alliances['red']['score']
            blue_score = match.alliances['blue']['score']
            win_score = max(red_score, blue_score)

            winning_scores += win_score
            win_margins += (win_score - min(red_score, blue_score))
            total_scores += red_score + blue_score

            if win_score > high_score[0]:
                high_score = [win_score, match.key_name, match.short_name]

            for alliance_color in ['red', 'blue']:
                try:
                    alliance_breakdown = match.score_breakdown[alliance_color]

                    auto_scores += alliance_breakdown['autoPoints']
                    crossing_scores += alliance_breakdown['teleopCrossingPoints']
                    boulder_scores += alliance_breakdown['teleopBoulderPoints']
                    tower_scores += alliance_breakdown['teleopChallengePoints'] + alliance_breakdown['teleopScalePoints']
                    foul_scores += alliance_breakdown['foulPoints']

                    pos1 = 'LowBar'
                    pos2 = alliance_breakdown['position2']
                    pos3 = alliance_breakdown['position3']
                    pos4 = alliance_breakdown['position4']
                    pos5 = alliance_breakdown['position5']
                    positions = [pos1, pos2, pos3, pos4, pos5]

                    for pos_idx, pos in enumerate(positions):
                        defense_opportunities[pos] += 1
                        if alliance_breakdown['position{}crossings'.format(pos_idx + 1)] == 2:
                            defense_damaged[pos] += 1

                    breaches += 1 if alliance_breakdown['teleopDefensesBreached'] else 0
                    high_goals += alliance_breakdown['autoBouldersHigh'] + alliance_breakdown['teleopBouldersHigh']
                    low_goals += alliance_breakdown['autoBouldersLow'] + alliance_breakdown['teleopBouldersLow']
                    captures += 1 if alliance_breakdown['teleopTowerCaptured'] else 0

                    for tower_face in ['towerFaceA', 'towerFaceB', 'towerFaceC']:
                        if alliance_breakdown[tower_face] == 'Challenged':
                            challenges += 1
                        elif alliance_breakdown[tower_face] == 'Scaled':
                            scales += 1
                    has_insights = True
                except Exception, e:
                    logging.warning("Event insights failed for {}".format(match.key.id()))
            finished_matches += 1

        if not has_insights:
            return None

        if finished_matches == 0:
            return {}

        opportunities_1x = 2 * finished_matches  # once per alliance
        opportunities_3x = 6 * finished_matches  # 3x per alliance
        event_insights = {
            'LowBar': [0, 0, 0],
            'A_ChevalDeFrise': [0, 0, 0],
            'A_Portcullis': [0, 0, 0],
            'B_Ramparts': [0, 0, 0],
            'B_Moat': [0, 0, 0],
            'C_SallyPort': [0, 0, 0],
            'C_Drawbridge': [0, 0, 0],
            'D_RoughTerrain': [0, 0, 0],
            'D_RockWall': [0, 0, 0],
            'average_high_goals': float(high_goals) / (2 * finished_matches),
            'average_low_goals': float(low_goals) / (2 * finished_matches),
            'breaches': [breaches, opportunities_1x, 100.0 * float(breaches) / opportunities_1x],  # [# success, # opportunities, %]
            'scales': [scales, opportunities_3x, 100.0 * float(scales) / opportunities_3x],
            'challenges': [challenges, opportunities_3x, 100.0 * float(challenges) / opportunities_3x],
            'captures': [captures, opportunities_1x, 100.0 * float(captures) / opportunities_1x],
            'average_win_score': float(winning_scores) / finished_matches,
            'average_win_margin': float(win_margins) / finished_matches,
            'average_score': float(total_scores) / (2 * finished_matches),
            'average_auto_score': float(auto_scores) / (2 * finished_matches),
            'average_crossing_score': float(crossing_scores) / (2 * finished_matches),
            'average_boulder_score': float(boulder_scores) / (2 * finished_matches),
            'average_tower_score': float(tower_scores) / (2 * finished_matches),
            'average_foul_score': float(foul_scores) / (2 * finished_matches),
            'high_score': high_score,  # [score, match key, match name]
        }
        for defense, opportunities in defense_opportunities.items():
            event_insights[defense] = [defense_damaged[defense], opportunities, 100.0 * float(defense_damaged[defense]) / opportunities]  # [# damaged, # opportunities, %]

        return event_insights
