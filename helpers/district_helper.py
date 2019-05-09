import copy
import logging
import heapq
import math

from collections import defaultdict

from google.appengine.ext import ndb

from consts.award_type import AwardType
from consts.district_point_values import DistrictPointValues
from consts.event_type import EventType

from database.team_query import DistrictTeamsQuery

from helpers.event_helper import EventHelper

from models.award import Award
from models.district_team import DistrictTeam
from models.match import Match


class DistrictHelper(object):
    """
    Point calculations based on:
    2014: http://www.usfirst.org/sites/default/files/uploadedFiles/Robotics_Programs/FRC/Resources/FRC_District_Standard_Points_Ranking_System.pdf
    2015: http://www.usfirst.org/sites/default/files/uploadedFiles/Robotics_Programs/FRC/Game_and_Season__Info/2015/FRC_District_Standard_Points_Ranking_System_2015%20Summary.pdf
    2016: https://firstfrc.blob.core.windows.net/frc2016manuals/AdminManual/FRC-2016-admin-manual.pdf
    """
    @classmethod
    def inverf(cls, x):
        if x > 0:
            s = 1
        elif x < 0:
            s = -1
        else:
            s = 0
        a = 0.147
        y = s * math.sqrt((math.sqrt((((2 / (math.pi * a)) + ((math.log(1 - x**2)) / 2))**2) - ((math.log(1 - x**2)) / a))) - ((2 / (math.pi * a)) + (math.log(1 - x**2)) / 2))
        return y

    @classmethod
    def calculate_event_points(cls, event):
        event.get_awards_async()
        event.get_matches_async()

        # Typically 3 for District CMP, 1 otherwise
        use_dcmp_multiplier = event.event_type_enum == EventType.DISTRICT_CMP or event.event_type_enum == EventType.DISTRICT_CMP_DIVISION
        POINTS_MULTIPLIER = DistrictPointValues.DISTRICT_CMP_MULTIPLIER.get(
            event.year, DistrictPointValues.DISTRICT_CMP_MULIPLIER_DEFAULT
        ) if use_dcmp_multiplier else DistrictPointValues.STANDARD_MULTIPLIER

        district_points = {
            'points': defaultdict(lambda: {
                'qual_points': 0,
                'elim_points': 0,
                'alliance_points': 0,
                'award_points': 0,
                'total': 0,
            }),
            'tiebreakers': defaultdict(lambda: {  # for tiebreaker stats that can't be calculated with 'points'
                'qual_wins': 0,
                'highest_qual_scores': [],
            }),
        }

        # match points
        if event.year >= 2015:
            # Switched to ranking-based points for 2015 and onward
            cls.calc_rank_based_match_points(event, district_points, event.matches, POINTS_MULTIPLIER)
        else:
            cls.calc_wlt_based_match_points(district_points, event.matches, POINTS_MULTIPLIER)

        # alliance points
        if event.event_type_enum == EventType.DISTRICT_CMP and event.divisions:
            # If this is a DCMP that has divisions, there are no alliance points
            # awarded, since a team would have got them in the division already
            pass
        elif event.alliance_selections:
            selection_points = EventHelper.alliance_selections_to_points(event, POINTS_MULTIPLIER, event.alliance_selections)
            for team, points in selection_points.items():
                district_points['points'][team]['alliance_points'] += points
        else:
            logging.info("Event {} has no alliance selection district_points!".format(event.key.id()))

        # award points
        for award in event.awards:
            point_value = 0
            if event.year >= 2014:
                if award.award_type_enum not in AwardType.NON_JUDGED_NON_TEAM_AWARDS:
                    if award.award_type_enum == AwardType.CHAIRMANS:
                        point_value = DistrictPointValues.CHAIRMANS.get(event.year, DistrictPointValues.CHAIRMANS_DEFAULT)
                    elif award.award_type_enum in {AwardType.ENGINEERING_INSPIRATION, AwardType.ROOKIE_ALL_STAR}:
                        point_value = DistrictPointValues.EI_AND_RAS_DEFAULT
                    else:
                        point_value = DistrictPointValues.OTHER_AWARD_DEFAULT
            else:  # Legacy awards
                if award.award_type_enum in DistrictPointValues.LEGACY_5_PT_AWARDS.get(event.year, []):
                    point_value = 5
                elif award.award_type_enum in DistrictPointValues.LEGACY_2_PT_AWARDS.get(event.year, []):
                    point_value = 2

            # Add award points to all teams who won
            if point_value:
                for team in award.team_list:
                    district_points['points'][team.id()]['award_points'] += point_value * POINTS_MULTIPLIER

        for team, point_breakdown in district_points['points'].items():
            for p in point_breakdown.values():
                district_points['points'][team]['total'] += p

        return district_points

    @classmethod
    def calculate_rankings(cls, events, teams, year):
        # aggregate points from first two events and district championship
        team_attendance_count = defaultdict(int)
        team_totals = defaultdict(lambda: {
            'event_points': [],
            'point_total': 0,
            'tiebreakers': 5 * [0] + [[]],  # there are 6 different tiebreakers
        })
        for event in events:
            if event.district_points is not None:
                for team_key in set(event.district_points['points'].keys()).union(set(event.district_points['tiebreakers'].keys())):
                    team_attendance_count[team_key] += 1
                    if team_attendance_count[team_key] <= 2 or event.event_type_enum == EventType.DISTRICT_CMP or event.event_type_enum == EventType.DISTRICT_CMP_DIVISION:
                        if team_key in event.district_points['points']:
                            team_totals[team_key]['event_points'].append((event, event.district_points['points'][team_key]))
                            team_totals[team_key]['point_total'] += event.district_points['points'][team_key]['total']

                            # add tiebreakers in order
                            team_totals[team_key]['tiebreakers'][0] += event.district_points['points'][team_key]['elim_points']
                            team_totals[team_key]['tiebreakers'][1] = max(event.district_points['points'][team_key]['elim_points'], team_totals[team_key]['tiebreakers'][1])
                            team_totals[team_key]['tiebreakers'][2] += event.district_points['points'][team_key]['alliance_points']
                            team_totals[team_key]['tiebreakers'][3] = max(event.district_points['points'][team_key]['qual_points'], team_totals[team_key]['tiebreakers'][3])

                        if team_key in event.district_points['tiebreakers']:  # add more tiebreakers
                            team_totals[team_key]['tiebreakers'][4] += event.district_points['tiebreakers'][team_key]['qual_wins']
                            team_totals[team_key]['tiebreakers'][5] = heapq.nlargest(3, event.district_points['tiebreakers'][team_key]['highest_qual_scores'] + team_totals[team_key]['tiebreakers'][5])

        # adding in rookie bonus
        # save valid team keys
        valid_team_keys = set()
        if type(teams) == ndb.tasklets.Future:
            teams = teams.get_result()
        for team in teams:
            if type(team) == ndb.tasklets.Future:
                team = team.get_result()
            bonus = 0
            if team.rookie_year == year:
                bonus = 10
            elif team.rookie_year == year - 1:
                bonus = 5
            team_totals[team.key.id()]['rookie_bonus'] = bonus
            team_totals[team.key.id()]['point_total'] += bonus

            valid_team_keys.add(team.key.id())

        team_totals = sorted(team_totals.items(),
            key=lambda (_, totals): [
                -totals['point_total'],
                -totals['tiebreakers'][0],
                -totals['tiebreakers'][1],
                -totals['tiebreakers'][2],
                -totals['tiebreakers'][3],
                -totals['tiebreakers'][4]] + [-score for score in totals['tiebreakers'][5]]
            )

        return filter(lambda (team_key, _): team_key in valid_team_keys, team_totals)

    @classmethod
    def calc_elim_match_points(cls, district_points, matches, POINTS_MULTIPLIER):
        elim_num_wins = defaultdict(lambda: defaultdict(int))
        elim_alliances = defaultdict(lambda: defaultdict(list))
        for match in matches:
            if not match.has_been_played or match.winning_alliance == '':
                # Skip unplayed matches
                continue

            match_set_key = '{}_{}{}'.format(match.event.id(), match.comp_level, match.set_number)
            elim_num_wins[match_set_key][match.winning_alliance] += 1
            elim_alliances[match_set_key][match.winning_alliance] += match.alliances[match.winning_alliance]['teams']

            # Add in points for elim match wins. Probably doesn't account for backup bots well
            # 2016-03-07: Maybe this does work for backup bots? -Eugene
            if elim_num_wins[match_set_key][match.winning_alliance] >= 2:
                for team in elim_alliances[match_set_key][match.winning_alliance]:
                    point_value = 0
                    if match.comp_level == 'qf':
                        point_value = DistrictPointValues.QF_WIN.get(match.year, DistrictPointValues.QF_WIN_DEFAULT) * POINTS_MULTIPLIER
                    elif match.comp_level == 'sf':
                        point_value = DistrictPointValues.SF_WIN.get(match.year, DistrictPointValues.SF_WIN_DEFAULT) * POINTS_MULTIPLIER
                    elif match.comp_level == 'f':
                        point_value = DistrictPointValues.F_WIN.get(match.year, DistrictPointValues.F_WIN_DEFAULT) * POINTS_MULTIPLIER
                    district_points['points'][team]['elim_points'] += point_value

    @classmethod
    def calc_elim_match_points_2015(cls, district_points, matches, POINTS_MULTIPLIER):
        from helpers.match_helper import MatchHelper  # circular import issue
        from helpers.playoff_advancement_helper import PlayoffAdvancementHelper

        # count number of matches played per team per comp level
        num_played = defaultdict(lambda: defaultdict(int))
        for level in ['qf', 'sf']:
            for match in matches[level]:
                if not match.has_been_played:
                    continue
                for color in ['red', 'blue']:
                    for team in match.alliances[color]['teams']:
                        num_played[level][team] += 1

        # qf and sf points
        advancement = PlayoffAdvancementHelper.generatePlayoffAdvancement2015(matches)
        for last_level, level in [('qf', 'sf'), ('sf', 'f')]:
            for (teams, _, _, _) in advancement[last_level]:
                teams = ['frc{}'.format(t) for t in teams]
                done = False
                for match in matches[level]:
                    for color in ['red', 'blue']:
                        if set(teams).intersection(set(match.alliances[color]['teams'])) != set():
                            for team in teams:
                                points = DistrictPointValues.QF_WIN.get(match.year, DistrictPointValues.QF_WIN_DEFAULT) if last_level == 'qf' else DistrictPointValues.SF_WIN.get(match.year, DistrictPointValues.SF_WIN_DEFAULT)
                                district_points['points'][team]['elim_points'] += int(
                                    math.ceil(points * num_played[last_level][team])) * POINTS_MULTIPLIER
                            done = True
                            break
                        if done:
                            break
                    if done:
                        break

        # final points
        num_wins = {'red': 0, 'blue': 0}
        team_matches_played = {'red': [], 'blue': []}
        for match in matches['f']:
            if not match.has_been_played or match.winning_alliance == '':
                continue

            num_wins[match.winning_alliance] += 1
            for team in match.alliances[match.winning_alliance]['teams']:
                team_matches_played[match.winning_alliance].append(team)

            if num_wins[match.winning_alliance] >= 2:
                points = DistrictPointValues.F_WIN.get(match.year, DistrictPointValues.F_WIN_DEFAULT)
                for team in team_matches_played[match.winning_alliance]:
                    district_points['points'][team]['elim_points'] += points * POINTS_MULTIPLIER

    @classmethod
    def calc_wlt_based_match_points(cls, district_points, matches, POINTS_MULTIPLIER):
        """
        Calculates match district points based on team record (wins, losses, ties)
        This algorithm was used prior to the 2015 season
        """
        elim_matches = []
        for match in matches:
            if not match.has_been_played:
                continue

            if match.comp_level == 'qm':  # Qual match points
                if match.winning_alliance == '':  # Match is a tie
                    for team in match.team_key_names:
                        district_points['points'][team]['qual_points'] += DistrictPointValues.MATCH_TIE * POINTS_MULTIPLIER
                else:  # Somebody won the match
                    for team in match.alliances[match.winning_alliance]['teams']:
                        district_points['points'][team]['qual_points'] += DistrictPointValues.MATCH_WIN * POINTS_MULTIPLIER
                        district_points['tiebreakers'][team]['qual_wins'] += 1

                for color in ['red', 'blue']:
                    for team in match.alliances[color]['teams']:
                        score = match.alliances[color]['score']
                        district_points['tiebreakers'][team]['highest_qual_scores'] = heapq.nlargest(3, district_points['tiebreakers'][team]['highest_qual_scores'] + [score])
                        # Make sure that teams without wins don't get dropped from 'points'
                        district_points['points'][team]['qual_points'] += 0
            else:  # Elim match points
                elim_matches.append(match)
        cls.calc_elim_match_points(district_points, elim_matches, POINTS_MULTIPLIER)

    @classmethod
    def calc_rank_based_match_points(cls, event, district_points, matches, POINTS_MULTIPLIER):
        """
        Calculates match district points based on team ranking
        This algorithm was introduced for the 2015 season and also used for 2016
        See: http://www.firstinspires.org/node/7616 and also
        http://www.firstinspires.org/robotics/frc/blog/Admin-Manual-Section-7-and-the-FIRST-STRONGHOLD-Logo
        """
        from helpers.match_helper import MatchHelper  # circular import issue

        # qual match points are calculated by rank
        rankings = event.details and event.details.rankings2
        if rankings:
            num_teams = len(rankings)
            alpha = 1.07
            for ranking in rankings:
                rank = ranking['rank']
                team = ranking['team_key']
                qual_points = int(math.ceil(cls.inverf(float(num_teams - 2 * rank + 2) / (alpha * num_teams)) * (
                10.0 / cls.inverf(1.0 / alpha)) + 12))
                district_points['points'][team]['qual_points'] = qual_points * POINTS_MULTIPLIER
        else:
            logging.info("Event {} has no rankings for qual_points calculations!".format(event.key.id()))

        matches = MatchHelper.organizeMatches(matches)

        # qual match calculations. only used for tiebreaking
        for match in matches['qm']:
            for color in ['red', 'blue']:
                for team in match.alliances[color]['teams']:
                    score = match.alliances[color]['score']
                    district_points['tiebreakers'][team]['highest_qual_scores'] = heapq.nlargest(3, district_points[
                        'tiebreakers'][team]['highest_qual_scores'] + [score])

        # elim match point calculations
        if event.year == 2015:
            cls.calc_elim_match_points_2015(district_points, matches, POINTS_MULTIPLIER)
        else:
            elim_matches = matches.get('qf', []) + matches.get('sf', []) + matches.get('f', [])
            cls.calc_elim_match_points(district_points, elim_matches, POINTS_MULTIPLIER)
