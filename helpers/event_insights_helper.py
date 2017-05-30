import logging
import traceback

from collections import defaultdict
from consts.event_type import EventType


class EventInsightsHelper(object):
    @classmethod
    def calculate_event_insights(cls, matches, year):
        INSIGHTS_MAP = {
            2016: cls.calculate_event_insights_2016,
            2017: cls.calculate_event_insights_2017,
        }

        if year in INSIGHTS_MAP:
            return INSIGHTS_MAP[year](matches)
        else:
            return None

    @classmethod
    def calculate_event_insights_2017(cls, matches):
        qual_matches = []
        playoff_matches = []
        for match in matches:
            if match.comp_level == 'qm':
                qual_matches.append(match)
            else:
                playoff_matches.append(match)

        qual_insights = cls._calculate_event_insights_2017_helper(qual_matches)
        playoff_insights = cls._calculate_event_insights_2017_helper(playoff_matches)

        return {
            'qual': qual_insights,
            'playoff': playoff_insights,
        }

    @classmethod
    def _calculate_event_insights_2017_helper(cls, matches):
        # Auto
        mobility_points_auto = 0
        rotor_points_auto = 0
        high_goals_auto = 0
        low_goals_auto = 0
        fuel_points_auto = 0
        points_auto = 0
        mobility_counts = 0

        # Teleop
        rotor_points_teleop = 0
        high_goals_teleop = 0
        low_goals_teleop = 0
        fuel_points_teleop = 0
        takeoff_points_teleop = 0
        points_teleop = 0
        takeoff_counts = 0

        # Overall
        rotor_1_engaged_auto = 0
        rotor_2_engaged_auto = 0
        rotor_1_engaged = 0
        rotor_2_engaged = 0
        rotor_3_engaged = 0
        rotor_4_engaged = 0
        rotor_points = 0
        high_goals = 0
        low_goals = 0
        fuel_points = 0

        kpa_achieved = 0
        unicorn_matches = 0

        winning_scores = 0
        win_margins = 0
        total_scores = 0
        foul_scores = 0
        high_kpa = [0, "", ""]  # score, match key, match name
        high_score = [0, "", ""]  # kpa, match key, match name

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

                    # High kPa
                    kpa = alliance_breakdown['autoFuelPoints'] + alliance_breakdown['teleopFuelPoints']
                    if kpa > high_kpa[0]:
                        high_kpa = [kpa, match.key_name, match.short_name]

                    # Auto
                    mobility_points_auto += alliance_breakdown['autoMobilityPoints']
                    rotor_points_auto += alliance_breakdown['autoRotorPoints']
                    fuel_points_auto += alliance_breakdown['autoFuelPoints']
                    high_goals_auto += alliance_breakdown['autoFuelHigh']
                    low_goals_auto += alliance_breakdown['autoFuelLow']
                    points_auto += alliance_breakdown['autoPoints']
                    for i in xrange(3):
                        mobility_counts += 1 if alliance_breakdown['robot{}Auto'.format(i+1)] == 'Mobility' else 0

                    # Teleop
                    rotor_points_teleop += alliance_breakdown['teleopRotorPoints']
                    fuel_points_teleop += alliance_breakdown['teleopFuelPoints']
                    high_goals_teleop += alliance_breakdown['teleopFuelHigh']
                    low_goals_teleop += alliance_breakdown['teleopFuelLow']
                    takeoff_points_teleop += alliance_breakdown['teleopTakeoffPoints']
                    points_teleop += alliance_breakdown['teleopPoints']
                    takeoff_counts += 1 if alliance_breakdown['touchpadFar'] == 'ReadyForTakeoff' else 0
                    takeoff_counts += 1 if alliance_breakdown['touchpadMiddle'] == 'ReadyForTakeoff' else 0
                    takeoff_counts += 1 if alliance_breakdown['touchpadNear'] == 'ReadyForTakeoff' else 0

                    # Overall
                    rotor_1_engaged_auto += 1 if alliance_breakdown['rotor1Auto'] else 0
                    rotor_2_engaged_auto += 1 if alliance_breakdown['rotor2Auto'] else 0
                    rotor_1_engaged += 1 if alliance_breakdown['rotor1Engaged'] else 0
                    rotor_2_engaged += 1 if alliance_breakdown['rotor2Engaged'] else 0
                    rotor_3_engaged += 1 if alliance_breakdown['rotor3Engaged'] else 0
                    rotor_4_engaged += 1 if alliance_breakdown['rotor4Engaged'] else 0
                    rotor_points += alliance_breakdown['autoRotorPoints'] + alliance_breakdown['teleopRotorPoints']
                    high_goals += alliance_breakdown['autoFuelHigh'] + alliance_breakdown['teleopFuelHigh']
                    low_goals += alliance_breakdown['autoFuelLow'] + alliance_breakdown['teleopFuelLow']
                    fuel_points += alliance_breakdown['autoFuelPoints'] + alliance_breakdown['teleopFuelPoints']

                    kpa_bonus = alliance_breakdown['kPaRankingPointAchieved'] or alliance_breakdown['kPaBonusPoints'] > 0
                    kpa_achieved += 1 if kpa_bonus else 0

                    alliance_win = alliance_color == match.winning_alliance
                    unicorn_matches += 1 if alliance_win and kpa_bonus and alliance_breakdown['rotor4Engaged'] else 0

                    foul_scores += alliance_breakdown['foulPoints']
                    has_insights = True
                except Exception, e:
                    msg = "Event insights failed for {}".format(match.key.id())
                    # event.get() below should be cheap since it's backed by context cache
                    if match.event.get().event_type_enum in EventType.SEASON_EVENT_TYPES:
                        logging.warning(msg)
                        logging.warning(traceback.format_exc())
                    else:
                        logging.info(msg)
            finished_matches += 1

        if not has_insights:
            return None

        if finished_matches == 0:
            return {}

        opportunities_1x = 2 * finished_matches  # once per alliance
        opportunities_3x = 6 * finished_matches  # 3x per alliance
        event_insights = {
            # Auto
            'average_mobility_points_auto': float(mobility_points_auto) / (2 * finished_matches),
            'average_rotor_points_auto': float(rotor_points_auto) / (2 * finished_matches),
            'average_fuel_points_auto': float(fuel_points_auto) / (2 * finished_matches),
            'average_high_goals_auto': float(high_goals_auto) / (2 * finished_matches),
            'average_low_goals_auto': float(low_goals_auto) / (2 * finished_matches),
            'average_points_auto': float(points_auto) / (2 * finished_matches),
            'mobility_counts': [mobility_counts, opportunities_3x, 100.0 * float(mobility_counts) / opportunities_3x],
            # Teleop
            'average_rotor_points_teleop': float(rotor_points_teleop) / (2 * finished_matches),
            'average_fuel_points_teleop': float(fuel_points_teleop) / (2 * finished_matches),
            'average_high_goals_teleop': float(high_goals_teleop) / (2 * finished_matches),
            'average_low_goals_teleop': float(low_goals_teleop) / (2 * finished_matches),
            'average_takeoff_points_teleop': float(takeoff_points_teleop) / (2 * finished_matches),
            'average_points_teleop': float(points_teleop) / (2 * finished_matches),
            'takeoff_counts': [takeoff_counts, opportunities_3x, 100.0 * float(takeoff_counts) / opportunities_3x],
            # Overall
            'average_rotor_points': float(rotor_points) / (2 * finished_matches),
            'average_fuel_points': float(fuel_points) / (2 * finished_matches),
            'average_high_goals': float(high_goals) / (2 * finished_matches),
            'average_low_goals': float(low_goals) / (2 * finished_matches),
            'rotor_1_engaged_auto': [rotor_1_engaged_auto, opportunities_1x, 100.0 * float(rotor_1_engaged_auto) / opportunities_1x],
            'rotor_2_engaged_auto': [rotor_2_engaged_auto, opportunities_1x, 100.0 * float(rotor_2_engaged_auto) / opportunities_1x],
            'rotor_1_engaged': [rotor_1_engaged, opportunities_1x, 100.0 * float(rotor_1_engaged) / opportunities_1x],
            'rotor_2_engaged': [rotor_2_engaged, opportunities_1x, 100.0 * float(rotor_2_engaged) / opportunities_1x],
            'rotor_3_engaged': [rotor_3_engaged, opportunities_1x, 100.0 * float(rotor_3_engaged) / opportunities_1x],
            'rotor_4_engaged': [rotor_4_engaged, opportunities_1x, 100.0 * float(rotor_4_engaged) / opportunities_1x],
            'kpa_achieved': [kpa_achieved, opportunities_1x, 100.0 * float(kpa_achieved) / opportunities_1x],
            'unicorn_matches': [unicorn_matches, opportunities_1x, 100.0 * float(unicorn_matches) / opportunities_1x],
            'average_win_score': float(winning_scores) / finished_matches,
            'average_win_margin': float(win_margins) / finished_matches,
            'average_score': float(total_scores) / (2 * finished_matches),
            'average_foul_score': float(foul_scores) / (2 * finished_matches),
            'high_score': high_score,  # [score, match key, match name]
            'high_kpa': high_kpa,  # [kpa, match key, match name]
        }

        return event_insights

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
                    msg = "Event insights failed for {}".format(match.key.id())
                    # event.get() below should be cheap since it's backed by context cache
                    if match.event.get().event_type_enum in EventType.SEASON_EVENT_TYPES:
                        logging.warning(msg)
                    else:
                        logging.info(msg)
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
