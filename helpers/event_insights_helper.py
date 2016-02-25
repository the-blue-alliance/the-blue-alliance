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

        finished_matches = 0
        for match in matches:
            for alliance_color in ['red', 'blue']:
                try:
                    alliance_breakdown = match.score_breakdown[alliance_color]

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

                    finished_matches += 1
                except Exception, e:
                    logging.error("Event insights failed for {}".format(match.key.id()))
        if finished_matches == 0:
            return None

        opportunities_1x = 2 * len(matches)  # once per alliance
        opportunities_3x = 6 * len(matches)  # 3x per alliance
        event_insights = {
            'high_goals': high_goals,
            'low_goals': low_goals,
            'breaches': [breaches, opportunities_1x, 100.0 * float(breaches) / opportunities_1x],  # [# success, # opportunities, %]
            'scales': [scales, opportunities_3x, 100.0 * float(scales) / opportunities_3x],
            'challenges': [challenges, opportunities_3x, 100.0 * float(challenges) / opportunities_3x],
            'captures': [captures, opportunities_1x, 100.0 * float(captures) / opportunities_1x],
        }
        for defense, opportunities in defense_opportunities.items():
            event_insights[defense] = [defense_damaged[defense], opportunities, 100.0 * float(defense_damaged[defense]) / opportunities]  # [# damaged, # opportunities, %]

        return event_insights
