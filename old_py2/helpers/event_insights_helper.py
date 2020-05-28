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
            2018: cls.calculate_event_insights_2018,
            2019: cls.calculate_event_insights_2019,
            2020: cls.calculate_event_insights_2020,
        }

        if year in INSIGHTS_MAP:
            return INSIGHTS_MAP[year](matches)
        else:
            return None

    @classmethod
    def calculate_event_insights_2020(cls, matches):
        qual_matches = []
        playoff_matches = []
        for match in matches:
            if match.comp_level == 'qm':
                qual_matches.append(match)
            else:
                playoff_matches.append(match)

        qual_insights = cls._calculate_event_insights_2020_helper(qual_matches)
        playoff_insights = cls._calculate_event_insights_2020_helper(playoff_matches)

        return {
            'qual': qual_insights,
            'playoff': playoff_insights,
        }

    @classmethod
    def _calculate_event_insights_2020_helper(cls, matches):
        # Auto
        init_line_auto = 0
        cell_count_bottom_auto = 0
        cell_count_outer_auto = 0
        cell_count_inner_auto = 0
        cell_points_auto = 0
        points_auto = 0

        # Teleop
        climb_park_teleop = 0
        robots_hanging = 0
        cell_count_bottom_teleop = 0
        cell_count_outer_teleop = 0
        cell_count_inner_teleop = 0
        cell_points_teleop = 0
        control_panel_points = 0
        points_teleop = 0

        # Overall
        exit_init_line_count = 0
        achieve_stage1_count = 0
        achieve_stage2_count = 0
        achieve_stage3_count = 0
        park_count = 0
        hang_count = 0
        generator_level_count = 0
        generator_operational_count = 0
        generator_energized_count = 0

        unicorn_matches = 0
        winning_scores = 0
        win_margins = 0
        total_scores = 0
        total_cell = 0
        foul_scores = 0
        high_score = [0, "", ""]

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
                isRed = alliance_color == 'red'
                try:
                    alliance_breakdown  = match.score_breakdown[alliance_color]

                    # Auto
                    init_line_auto += alliance_breakdown['autoInitLinePoints']
                    cell_count_bottom_auto += alliance_breakdown['autoCellsBottom']
                    cell_count_outer_auto += alliance_breakdown['autoCellsOuter']
                    cell_count_inner_auto += alliance_breakdown['autoCellsInner']
                    cell_points_auto += alliance_breakdown['autoCellPoints']
                    points_auto += alliance_breakdown['autoPoints']

                    # Teleop
                    climb_park_teleop += alliance_breakdown['endgamePoints']
                    robots_hanging += alliance_breakdown['tba_numRobotsHanging']
                    cell_count_bottom_teleop += alliance_breakdown['teleopCellsBottom']
                    cell_count_outer_teleop += alliance_breakdown['teleopCellsOuter']
                    cell_count_inner_teleop += alliance_breakdown['teleopCellsInner']
                    cell_points_teleop += alliance_breakdown['teleopCellPoints']
                    control_panel_points += alliance_breakdown['controlPanelPoints']
                    points_teleop += alliance_breakdown['teleopPoints']

                    # Overall
                    for i in xrange(3):
                        init_line = 'initLineRobot{}'.format(i+1)
                        if alliance_breakdown[init_line] == 'Exited':
                            exit_init_line_count += 1

                        endgame = 'endgameRobot{}'.format(i+1)
                        if alliance_breakdown[endgame] == 'Park':
                            park_count += 1
                        elif alliance_breakdown[endgame] == 'Hang':
                            hang_count += 1

                    achieve_stage1_count += 1 if alliance_breakdown['stage1Activated'] else 0
                    achieve_stage2_count += 1 if alliance_breakdown['stage2Activated'] else 0
                    achieve_stage3_count += 1 if alliance_breakdown['stage3Activated'] else 0
                    generator_level_count += 1 if alliance_breakdown['endgameRungIsLevel'] == 'IsLevel' and alliance_breakdown['tba_numRobotsHanging'] > 0 else 0
                    generator_operational_count += 1 if alliance_breakdown['shieldOperationalRankingPoint'] else 0
                    generator_energized_count += 1 if alliance_breakdown['shieldEnergizedRankingPoint'] else 0
                    total_cell += alliance_breakdown['autoCellPoints'] + alliance_breakdown['teleopCellPoints']

                    alliance_win = alliance_color == match.winning_alliance
                    unicorn_matches += (1 if alliance_win and alliance_breakdown['shieldOperationalRankingPoint'] and alliance_breakdown['shieldEnergizedRankingPoint'] else 0)
                    foul_scores += alliance_breakdown['foulPoints']
                    has_insights = True
                except Exception, e:
                    msg = "Event insights failed for {}: {}".format(match.key.id(), e.message)
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

        opportunities_1x = 2 * finished_matches
        opportunities_3x = 6 * finished_matches
        event_insights = {
            # Auto
            'average_init_line_points_auto': float(init_line_auto) / opportunities_1x,
            'average_cell_count_bottom_auto': float(cell_count_bottom_auto) / opportunities_1x,
            'average_cell_count_outer_auto': float(cell_count_outer_auto) / opportunities_1x,
            'average_cell_count_inner_auto': float(cell_count_inner_auto) / opportunities_1x,
            'average_cell_count_auto': float(cell_count_bottom_auto + cell_count_outer_auto + cell_count_inner_auto) / opportunities_1x,
            'average_cell_points_auto': float(cell_points_auto) / opportunities_1x,
            'average_points_auto': float(points_auto) / opportunities_1x,
            # Teleop
            'average_endgame_points': float(climb_park_teleop) / opportunities_1x,
            'average_num_robots_hanging': float(robots_hanging) / opportunities_1x,
            'average_cell_count_bottom_teleop': float(cell_count_bottom_teleop) / opportunities_1x,
            'average_cell_count_outer_teleop': float(cell_count_outer_teleop) / opportunities_1x,
            'average_cell_count_inner_teleop': float(cell_count_inner_teleop) / opportunities_1x,
            'average_cell_count_teleop': float(cell_count_bottom_teleop + cell_count_outer_teleop + cell_count_inner_teleop) / opportunities_1x,
            'average_cell_points_teleop': float(cell_points_teleop) / opportunities_1x,
            'average_control_panel_points': float(control_panel_points) / opportunities_1x,
            'average_points_teleop': float(points_teleop) / opportunities_1x,
            # Overall
            'exit_init_line_count': [exit_init_line_count, opportunities_3x, 100.0 * float(exit_init_line_count) / opportunities_3x],
            'achieve_stage1_count': [achieve_stage1_count, opportunities_1x, 100.0 * float(achieve_stage1_count) / opportunities_1x],
            'achieve_stage2_count': [achieve_stage2_count, opportunities_1x, 100.0 * float(achieve_stage2_count) / opportunities_1x],
            'achieve_stage3_count': [achieve_stage3_count, opportunities_1x, 100.0 * float(achieve_stage3_count) / opportunities_1x],
            'park_count': [park_count, opportunities_3x, 100.0 * float(park_count) / opportunities_3x],
            'hang_count': [hang_count, opportunities_3x, 100.0 * float(hang_count) / opportunities_3x],
            'generator_level_count': [generator_level_count, opportunities_1x, 100.0 * float(generator_level_count) / opportunities_1x],
            'generator_operational_rp_achieved': [generator_operational_count, opportunities_1x, 100.0 * float(generator_operational_count) / opportunities_1x],
            'generator_energized_rp_achieved': [generator_energized_count, opportunities_1x, 100.0 * float(generator_energized_count) / opportunities_1x],
            'unicorn_matches': [unicorn_matches, opportunities_1x, 100.0 * float(unicorn_matches) / opportunities_1x],
            'average_win_score': float(winning_scores) / finished_matches,
            'average_win_margin': float(win_margins) / finished_matches,
            'average_score': float(total_scores) / opportunities_1x,
            'average_cell_count_bottom': float(cell_count_bottom_auto + cell_count_bottom_teleop) / opportunities_1x,
            'average_cell_count_outer': float(cell_count_outer_auto + cell_count_outer_teleop) / opportunities_1x,
            'average_cell_count_inner': float(cell_count_inner_auto + cell_count_inner_teleop) / opportunities_1x,
            'average_cell_count': float(cell_count_bottom_auto + cell_count_outer_auto + cell_count_inner_auto + cell_count_bottom_teleop + cell_count_outer_teleop + cell_count_inner_teleop) / opportunities_1x,
            'average_cell_score': float(total_cell) / opportunities_1x,
            'average_foul_score': float(foul_scores) / opportunities_1x,
            'high_score': high_score,
        }
        return event_insights

    @classmethod
    def calculate_event_insights_2019(cls, matches):
        qual_matches = []
        playoff_matches = []
        for match in matches:
            if match.comp_level == 'qm':
                qual_matches.append(match)
            else:
                playoff_matches.append(match)

        qual_insights = cls._calculate_event_insights_2019_helper(qual_matches)
        playoff_insights = cls._calculate_event_insights_2019_helper(playoff_matches)

        return {
            'qual': qual_insights,
            'playoff': playoff_insights,
        }

    @classmethod
    def _calculate_event_insights_2019_helper(cls, matches):
        # Auto
        sandstorm_bonus_auto = 0
        points_auto = 0

        # Teleop
        hab_climb_teleop = 0
        points_teleop = 0

        # Overall
        cross_hab_line_count = 0
        cross_hab_line_sandstorm_count = 0
        complete_1_rocket_count = 0
        complete_2_rockets_count = 0

        cargo_ship_hatch_panel_preload_count = [0] * 6  # 0 starts from far left
        cargo_ship_cargo_preload_count = [0] * 6  # 0 starts from far left
        cargo_ship_hatch_panel_count = [0] * 8  # 0 starts from far left
        cargo_ship_cargo_count = [0] * 8  # 0 starts from far left
        rocket_hatch_panel_count = defaultdict(int)
        rocket_cargo_count = defaultdict(int)
        hatch_panel_points = 0
        cargo_points = 0
        level1_climb_count = 0
        level2_climb_count = 0
        level3_climb_count = 0

        # kpa_achieved = 0
        rocket_rp_achieved = 0
        climb_rp_achieved = 0
        unicorn_matches = 0

        winning_scores = 0
        win_margins = 0
        total_scores = 0
        foul_scores = 0
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
                isRed = alliance_color == 'red'
                try:
                    alliance_breakdown = match.score_breakdown[alliance_color]

                    # Auto
                    sandstorm_bonus_auto += alliance_breakdown['sandStormBonusPoints']
                    points_auto += alliance_breakdown['autoPoints']

                    # Teleop
                    hab_climb_teleop += alliance_breakdown['habClimbPoints']
                    points_teleop += alliance_breakdown['teleopPoints']

                    # Overall
                    for i in xrange(3):
                        hab_line = 'habLineRobot{}'.format(i+1)
                        if alliance_breakdown[hab_line] == 'CrossedHabLineInTeleop':
                            cross_hab_line_count += 1
                        elif alliance_breakdown[hab_line] == 'CrossedHabLineInSandstorm':
                            cross_hab_line_count += 1
                            cross_hab_line_sandstorm_count += 1

                        hab_climb = 'endgameRobot{}'.format(i+1)
                        if alliance_breakdown[hab_climb] == 'HabLevel1':
                            level1_climb_count += 1
                        elif alliance_breakdown[hab_climb] == 'HabLevel2':
                            level2_climb_count += 1
                        elif alliance_breakdown[hab_climb] == 'HabLevel3':
                            level3_climb_count += 1

                    complete_1_rocket_count += 1 if alliance_breakdown['completedRocketNear'] or alliance_breakdown['completedRocketFar'] else 0
                    complete_2_rockets_count += 1 if alliance_breakdown['completedRocketNear'] and alliance_breakdown['completedRocketFar'] else 0

                    if alliance_breakdown['preMatchBay1'] == 'Panel':
                        cargo_ship_hatch_panel_preload_count[0 if isRed else 5] += 1
                    else:
                        cargo_ship_cargo_preload_count[0 if isRed else 5] += 1
                    if alliance_breakdown['preMatchBay2'] == 'Panel':
                        cargo_ship_hatch_panel_preload_count[1 if isRed else 4] += 1
                    else:
                        cargo_ship_cargo_preload_count[1 if isRed else 4] += 1
                    if alliance_breakdown['preMatchBay3'] == 'Panel':
                        cargo_ship_hatch_panel_preload_count[2 if isRed else 3] += 1
                    else:
                        cargo_ship_cargo_preload_count[2 if isRed else 3] += 1
                    if alliance_breakdown['preMatchBay6'] == 'Panel':
                        cargo_ship_hatch_panel_preload_count[3 if isRed else 2] += 1
                    else:
                        cargo_ship_cargo_preload_count[3 if isRed else 2] += 1
                    if alliance_breakdown['preMatchBay7'] == 'Panel':
                        cargo_ship_hatch_panel_preload_count[4 if isRed else 1] += 1
                    else:
                        cargo_ship_cargo_preload_count[4 if isRed else 1] += 1
                    if alliance_breakdown['preMatchBay8'] == 'Panel':
                        cargo_ship_hatch_panel_preload_count[5 if isRed else 0] += 1
                    else:
                        cargo_ship_cargo_preload_count[5 if isRed else 0] += 1

                    for i in xrange(8):
                        idx = i if isRed else 7 - i
                        bay = 'bay{}'.format(i+1)
                        cargo_ship_hatch_panel_count[idx] += 1 if 'Panel' in alliance_breakdown[bay] else 0
                        cargo_ship_cargo_count[idx] += 1 if 'Cargo' in alliance_breakdown[bay] else 0

                    for LRSide in ['Left', 'Right']:  # Relative to Field
                        for NFSide in ['Near', 'Far']:  # Relative to Field
                            low = 'low{}Rocket{}'.format(LRSide, NFSide)
                            mid = 'mid{}Rocket{}'.format(LRSide, NFSide)
                            top = 'top{}Rocket{}'.format(LRSide, NFSide)

                            # Get alliance-relative sides
                            if NFSide == 'Near' and LRSide == 'Left':
                                alLRSide = 'Left' if isRed else 'Right'
                                alNFSide = 'Near' if isRed else 'Far'
                            elif NFSide == 'Near' and LRSide == 'Right':
                                alLRSide = 'Left' if isRed else 'Right'
                                alNFSide = 'Far' if isRed else 'Near'
                            elif NFSide == 'Far' and LRSide == 'Left':
                                alLRSide = 'Right' if isRed else 'Left'
                                alNFSide = 'Far' if isRed else 'Near'
                            elif NFSide == 'Far' and LRSide == 'Right':
                                alLRSide = 'Right' if isRed else 'Left'
                                alNFSide = 'Near' if isRed else 'Far'

                            rocket_hatch_panel_count['low{}{}'.format(alLRSide, alNFSide)] += 1 if 'Panel' in alliance_breakdown[low] else 0
                            rocket_hatch_panel_count['mid{}{}'.format(alLRSide, alNFSide)] += 1 if 'Panel' in alliance_breakdown[mid] else 0
                            rocket_hatch_panel_count['top{}{}'.format(alLRSide, alNFSide)] += 1 if 'Panel' in alliance_breakdown[top] else 0
                            rocket_cargo_count['low{}{}'.format(alLRSide, alNFSide)] += 1 if 'Cargo' in alliance_breakdown[low] else 0
                            rocket_cargo_count['mid{}{}'.format(alLRSide, alNFSide)] += 1 if 'Cargo' in alliance_breakdown[mid] else 0
                            rocket_cargo_count['top{}{}'.format(alLRSide, alNFSide)] += 1 if 'Cargo' in alliance_breakdown[top] else 0

                    hatch_panel_points += alliance_breakdown['hatchPanelPoints']
                    cargo_points += alliance_breakdown['cargoPoints']

                    completed_rocket = alliance_breakdown['completedRocketNear'] or alliance_breakdown['completedRocketFar']
                    alliance_rocket_rp_achieved = alliance_breakdown['completeRocketRankingPoint'] or completed_rocket
                    alliance_climb_rp_achieved = alliance_breakdown['habDockingRankingPoint'] or (alliance_breakdown['habClimbPoints'] >= 15)
                    rocket_rp_achieved += 1 if alliance_rocket_rp_achieved else 0
                    climb_rp_achieved += 1 if alliance_climb_rp_achieved else 0
                    alliance_win = alliance_color == match.winning_alliance
                    unicorn_matches += 1 if (alliance_win and alliance_rocket_rp_achieved and alliance_climb_rp_achieved) else 0

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
        average_rocket_hatch_panel_count = {}
        for key, value in rocket_hatch_panel_count.items():
            average_rocket_hatch_panel_count[key] = 100 * float(value) / opportunities_1x
        average_rocket_cargo_count = {}
        for key, value in rocket_cargo_count.items():
            average_rocket_cargo_count[key] = 100 * float(value) / opportunities_1x
        event_insights = {
            # Auto
            'average_sandstorm_bonus_auto': float(sandstorm_bonus_auto) / (2 * finished_matches),
            'average_points_auto': float(points_auto) / (2 * finished_matches),
            # Teleop
            'average_hab_climb_teleop': float(hab_climb_teleop) / (2 * finished_matches),
            'average_points_teleop': float(points_teleop) / (2 * finished_matches),
            # Overall
            'cross_hab_line_count': [cross_hab_line_count, opportunities_3x, 100.0 * float(cross_hab_line_count) / opportunities_3x],
            'cross_hab_line_sandstorm_count': [cross_hab_line_sandstorm_count, opportunities_3x, 100.0 * float(cross_hab_line_sandstorm_count) / opportunities_3x],
            'level1_climb_count': [level1_climb_count, opportunities_3x, 100.0 * float(level1_climb_count) / opportunities_3x],
            'level2_climb_count': [level2_climb_count, opportunities_3x, 100.0 * float(level2_climb_count) / opportunities_3x],
            'level3_climb_count': [level3_climb_count, opportunities_3x, 100.0 * float(level3_climb_count) / opportunities_3x],
            'complete_1_rocket_count': [complete_1_rocket_count, opportunities_1x, 100.0 * float(complete_1_rocket_count) / opportunities_1x],
            'complete_2_rockets_count': [complete_2_rockets_count, opportunities_1x, 100.0 * float(complete_2_rockets_count) / opportunities_1x],
            'average_cargo_ship_hatch_panel_preload_count': [100.0 * float(x) / opportunities_1x for x in cargo_ship_hatch_panel_preload_count],
            'average_cargo_ship_cargo_preload_count': [100.0 * float(x) / opportunities_1x for x in cargo_ship_cargo_preload_count],
            'average_cargo_ship_hatch_panel_count': [100.0 * float(x) / opportunities_1x for x in cargo_ship_hatch_panel_count],
            'average_cargo_ship_cargo_count': [100.0 * float(x) / opportunities_1x for x in cargo_ship_cargo_count],
            'average_rocket_hatch_panel_count': average_rocket_hatch_panel_count,
            'average_rocket_cargo_count': average_rocket_cargo_count,
            'average_hatch_panel_points': float(hatch_panel_points) / opportunities_1x,
            'average_cargo_points': float(cargo_points) / opportunities_1x,
            'rocket_rp_achieved': [rocket_rp_achieved, opportunities_1x, 100.0 * float(rocket_rp_achieved) / opportunities_1x],
            'climb_rp_achieved': [climb_rp_achieved, opportunities_1x, 100.0 * float(climb_rp_achieved) / opportunities_1x],
            'unicorn_matches': [unicorn_matches, opportunities_1x, 100.0 * float(unicorn_matches) / opportunities_1x],
            'average_win_score': float(winning_scores) / finished_matches,
            'average_win_margin': float(win_margins) / finished_matches,
            'average_score': float(total_scores) / opportunities_1x,
            'average_foul_score': float(foul_scores) / opportunities_1x,
            'high_score': high_score,  # [score, match key, match name]
        }

        return event_insights

    @classmethod
    def calculate_event_insights_2018(cls, matches):
        qual_matches = []
        playoff_matches = []
        for match in matches:
            if match.comp_level == 'qm':
                qual_matches.append(match)
            else:
                playoff_matches.append(match)

        qual_insights = cls._calculate_event_insights_2018_helper(qual_matches)
        playoff_insights = cls._calculate_event_insights_2018_helper(playoff_matches)

        return {
            'qual': qual_insights,
            'playoff': playoff_insights,
        }

    @classmethod
    def _calculate_event_insights_2018_helper(cls, matches):
        # Auto
        run_points_auto = 0
        scale_ownership_time_auto = 0
        switch_ownership_time_auto = 0
        points_auto = 0

        run_counts_auto = 0
        switch_owned_counts_auto = 0

        # Teleop
        scale_ownership_time_teleop = 0
        switch_ownership_time_teleop = 0
        points_teleop = 0

        # Overall
        winning_scale_ownership_percentage_auto = 0
        winning_own_switch_ownership_percentage_auto = 0
        winning_scale_ownership_percentage_teleop = 0
        winning_own_switch_ownership_percentage_teleop = 0
        winning_opp_switch_denial_percentage_teleop = 0
        winning_scale_ownership_percentage = 0
        winning_own_switch_ownership_percentage = 0

        scale_neutral_percentage_auto = 0
        scale_neutral_percentage_teleop = 0
        scale_neutral_percentage = 0

        force_played = 0
        levitate_played = 0
        boost_played = 0
        force_played_counts = 0
        levitate_played_counts = 0
        boost_played_counts = 0
        vault_points = 0
        endgame_points = 0

        climb_counts = 0
        auto_quest_achieved = 0
        face_the_boss_achieved = 0
        unicorn_matches = 0

        winning_scores = 0
        win_margins = 0
        total_scores = 0
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
                    opp_alliance_breakdown = match.score_breakdown['red' if alliance_color == 'blue' else 'red']
                    alliance_win = alliance_color == match.winning_alliance

                    # Auto
                    run_points_auto += alliance_breakdown['autoRunPoints']
                    scale_ownership_time_auto += alliance_breakdown['autoScaleOwnershipSec']
                    switch_ownership_time_auto += alliance_breakdown['autoSwitchOwnershipSec']
                    points_auto += alliance_breakdown['autoPoints']

                    switch_owned_counts_auto += 1 if alliance_breakdown['autoSwitchAtZero'] else 0
                    alliance_run_counts_auto = 0
                    for i in xrange(3):
                        alliance_run_counts_auto += 1 if alliance_breakdown['autoRobot{}'.format(i+1)] == 'AutoRun' else 0
                    run_counts_auto += alliance_run_counts_auto

                    # Teleop
                    scale_ownership_time_teleop += alliance_breakdown['teleopScaleOwnershipSec']
                    switch_ownership_time_teleop += alliance_breakdown['teleopSwitchOwnershipSec']
                    points_teleop += alliance_breakdown['teleopPoints']

                    # Overall
                    if alliance_win:
                        winning_scale_ownership_percentage_auto += float(alliance_breakdown['autoScaleOwnershipSec']) / 15
                        winning_own_switch_ownership_percentage_auto += float(alliance_breakdown['autoSwitchOwnershipSec']) / 15

                        winning_scale_ownership_percentage_teleop += float(alliance_breakdown['teleopScaleOwnershipSec']) / 135
                        winning_own_switch_ownership_percentage_teleop += float(alliance_breakdown['teleopSwitchOwnershipSec']) / 135
                        winning_opp_switch_denial_percentage_teleop += float(135 - opp_alliance_breakdown['teleopSwitchOwnershipSec']) / 135

                        winning_scale_ownership_percentage += float(alliance_breakdown['autoScaleOwnershipSec'] + alliance_breakdown['teleopScaleOwnershipSec']) / 150
                        winning_own_switch_ownership_percentage += float(alliance_breakdown['autoSwitchOwnershipSec'] + alliance_breakdown['teleopSwitchOwnershipSec']) / 150

                    scale_neutral_percentage_auto += float(7.5 - alliance_breakdown['autoScaleOwnershipSec']) / 7.5
                    scale_neutral_percentage_teleop += float(67.5 - alliance_breakdown['teleopScaleOwnershipSec']) / 67.5
                    scale_neutral_percentage += float(75 - alliance_breakdown['autoScaleOwnershipSec'] - alliance_breakdown['teleopScaleOwnershipSec']) / 75

                    force_played += alliance_breakdown['vaultForcePlayed']
                    levitate_played += alliance_breakdown['vaultLevitatePlayed']
                    boost_played += alliance_breakdown['vaultBoostPlayed']
                    force_played_counts += alliance_breakdown['vaultForcePlayed'] > 0
                    levitate_played_counts += alliance_breakdown['vaultLevitatePlayed'] > 0
                    boost_played_counts += alliance_breakdown['vaultBoostPlayed'] > 0

                    vault_points += alliance_breakdown['vaultPoints']
                    endgame_points += alliance_breakdown['endgamePoints']

                    alliance_climb_levitate_counts = 0
                    for i in xrange(3):
                        alliance_climb_levitate_counts += 1 if alliance_breakdown['endgameRobot{}'.format(i+1)] in {'Climbing', 'Levitate'} else 0
                        climb_counts += 1 if alliance_breakdown['endgameRobot{}'.format(i+1)] == 'Climbing' else 0

                    alliance_auto_quest_achieved = alliance_run_counts_auto == 3 and alliance_breakdown['autoSwitchAtZero']
                    alliance_face_the_boss_achieved = alliance_climb_levitate_counts == 3
                    auto_quest_achieved += 1 if alliance_auto_quest_achieved else 0
                    face_the_boss_achieved += 1 if alliance_face_the_boss_achieved else 0
                    unicorn_matches += 1 if (alliance_win and alliance_auto_quest_achieved and alliance_face_the_boss_achieved) else 0

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
            'average_run_points_auto': float(run_points_auto) / (2 * finished_matches),
            'average_scale_ownership_points_auto': float(scale_ownership_time_auto * 2) / (2 * finished_matches),
            'average_switch_ownership_points_auto': float(switch_ownership_time_auto * 2) / (2 * finished_matches),
            'average_points_auto': float(points_auto) / (2 * finished_matches),

            'run_counts_auto': [run_counts_auto, opportunities_3x, 100.0 * float(run_counts_auto) / opportunities_3x],
            'switch_owned_counts_auto': [switch_owned_counts_auto, opportunities_1x, 100.0 * float(switch_owned_counts_auto) / opportunities_1x],

            # Teleop
            'average_scale_ownership_points_teleop': float(scale_ownership_time_teleop) / (2 * finished_matches),
            'average_switch_ownership_points_teleop': float(switch_ownership_time_teleop) / (2 * finished_matches),
            'average_points_teleop': float(points_teleop) / (2 * finished_matches),

            # Overall
            'climb_counts': [climb_counts, opportunities_3x, 100.0 * float(climb_counts) / opportunities_3x],
            'force_played_counts': [force_played_counts, opportunities_1x, 100.0 * float(force_played_counts) / opportunities_1x],
            'levitate_played_counts': [levitate_played_counts, opportunities_1x, 100.0 * float(levitate_played_counts) / opportunities_1x],
            'boost_played_counts': [boost_played_counts, opportunities_1x, 100.0 * float(boost_played_counts) / opportunities_1x],

            'average_scale_ownership_points': float(scale_ownership_time_auto * 2 + scale_ownership_time_teleop) / (2 * finished_matches),
            'average_switch_ownership_points': float(switch_ownership_time_auto * 2 + switch_ownership_time_teleop) / (2 * finished_matches),

            'winning_scale_ownership_percentage_auto': 100.0 * float(winning_scale_ownership_percentage_auto) / finished_matches,
            'winning_own_switch_ownership_percentage_auto': 100.0 * float(winning_own_switch_ownership_percentage_auto) / finished_matches,
            'winning_scale_ownership_percentage_teleop': 100.0 * float(winning_scale_ownership_percentage_teleop) / finished_matches,
            'winning_own_switch_ownership_percentage_teleop': 100.0 * float(winning_own_switch_ownership_percentage_teleop) / finished_matches,
            'winning_opp_switch_denial_percentage_teleop': 100.0 * float(winning_opp_switch_denial_percentage_teleop) / finished_matches,
            'winning_scale_ownership_percentage': 100.0 * float(winning_scale_ownership_percentage) / finished_matches,
            'winning_own_switch_ownership_percentage': 100.0 * float(winning_own_switch_ownership_percentage) / finished_matches,

            'scale_neutral_percentage_auto': 100.0 * float(scale_neutral_percentage_auto) / (2 * finished_matches),
            'scale_neutral_percentage_teleop': 100.0 * float(scale_neutral_percentage_teleop) / (2 * finished_matches),
            'scale_neutral_percentage': 100.0 * float(scale_neutral_percentage) / (2 * finished_matches),

            'average_force_played': float(force_played) / force_played_counts,
            'average_boost_played': float(boost_played) / boost_played_counts,
            'average_vault_points': float(vault_points) / (2 * finished_matches),
            'average_endgame_points': float(endgame_points) / (2 * finished_matches),

            'average_win_score': float(winning_scores) / finished_matches,
            'average_win_margin': float(win_margins) / finished_matches,
            'average_score': float(total_scores) / (2 * finished_matches),
            'average_foul_score': float(foul_scores) / (2 * finished_matches),
            'high_score': high_score,  # [score, match key, match name]
            'auto_quest_achieved': [auto_quest_achieved, opportunities_1x, 100.0 * float(auto_quest_achieved) / opportunities_1x],
            'face_the_boss_achieved': [face_the_boss_achieved, opportunities_1x, 100.0 * float(face_the_boss_achieved) / opportunities_1x],
            'unicorn_matches': [unicorn_matches, opportunities_1x, 100.0 * float(unicorn_matches) / opportunities_1x],
        }

        return event_insights

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
