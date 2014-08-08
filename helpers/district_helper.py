import logging
import heapq

from collections import defaultdict

from google.appengine.ext import ndb

from consts.award_type import AwardType
from consts.district_type import DistrictType
from consts.event_type import EventType

from helpers.event_helper import EventHelper

from models.award import Award
from models.match import Match

class DistrictHelper(object):
    """
    Point calculations based on: http://www.usfirst.org/sites/default/files/uploadedFiles/Robotics_Programs/FRC/Resources/FRC_District_Standard_Points_Ranking_System.pdf
    """
    @classmethod
    def calculate_event_points(cls, event):
        match_key_futures = Match.query(Match.event == event.key).fetch_async(None, keys_only=True)
        award_key_futures = Award.query(Award.event == event.key).fetch_async(None, keys_only=True)

        match_futures = ndb.get_multi_async(match_key_futures.get_result())
        award_futures = ndb.get_multi_async(award_key_futures.get_result())

        POINTS_MULTIPLIER = 3 if event.event_type_enum == EventType.DISTRICT_CMP else 1

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
        elim_num_wins = defaultdict(lambda: defaultdict(int))
        elim_alliances = defaultdict(lambda: defaultdict(list))
        for match_future in match_futures:
            match = match_future.get_result()
            if not match.has_been_played:
                continue

            if match.comp_level == 'qm':
                if match.winning_alliance == '':
                    for team in match.team_key_names:
                        district_points['points'][team]['qual_points'] += 1 * POINTS_MULTIPLIER
                else:
                    for team in match.alliances[match.winning_alliance]['teams']:
                        district_points['points'][team]['qual_points'] += 2 * POINTS_MULTIPLIER
                        district_points['tiebreakers'][team]['qual_wins'] += 1

                for color in ['red', 'blue']:
                    for team in match.alliances[color]['teams']:
                        score = match.alliances[color]['score']
                        district_points['tiebreakers'][team]['highest_qual_scores'] = heapq.nlargest(3, district_points['tiebreakers'][team]['highest_qual_scores'] + [score])
            else:
                if match.winning_alliance == '':
                    continue

                match_set_key = '{}_{}{}'.format(match.event.id(), match.comp_level, match.set_number)
                elim_num_wins[match_set_key][match.winning_alliance] += 1
                elim_alliances[match_set_key][match.winning_alliance] += match.alliances[match.winning_alliance]['teams']

                if elim_num_wins[match_set_key][match.winning_alliance] >= 2:
                    for team in elim_alliances[match_set_key][match.winning_alliance]:
                        district_points['points'][team]['elim_points'] += 5* POINTS_MULTIPLIER

        # alliance points
        if event.alliance_selections:
            selection_points = EventHelper.alliance_selections_to_points(event.alliance_selections)
            for team, points in selection_points.items():
                district_points['points'][team]['alliance_points'] += points * POINTS_MULTIPLIER
        else:
            logging.warning("Event {} has no alliance selection district_points!".format(event.key.id()))

        # award points
        for award_future in award_futures:
            award = award_future.get_result()
            if award.award_type_enum not in AwardType.NON_JUDGED_NON_TEAM_AWARDS:
                if award.award_type_enum == AwardType.CHAIRMANS:
                    point_value = 10
                elif award.award_type_enum in {AwardType.ENGINEERING_INSPIRATION, AwardType.ROOKIE_ALL_STAR}:
                    point_value = 8
                else:
                    point_value = 5
                for team in award.team_list:
                    district_points['points'][team.id()]['award_points'] += point_value * POINTS_MULTIPLIER

        for team, point_breakdown in district_points['points'].items():
            for p in point_breakdown.values():
                district_points['points'][team]['total'] += p

        return district_points


    @classmethod
    def calculate_rankings(cls, events, team_futures, year):
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
                    if team_attendance_count[team_key] <= 2 or event.event_type_enum == EventType.DISTRICT_CMP:
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
        for team_future in team_futures:
            team = team_future.get_result()
            bonus = None
            if team.rookie_year == year:
                bonus = 10
            elif team.rookie_year == year - 1:
                bonus = 5
            if bonus is not None:
                team_totals[team.key.id()]['rookie_bonus'] = bonus
                team_totals[team.key.id()]['point_total'] += bonus

        team_totals = sorted(team_totals.items(),
            key=lambda (_, totals): [
                -totals['point_total'],
                -totals['tiebreakers'][0],
                -totals['tiebreakers'][1],
                -totals['tiebreakers'][2],
                -totals['tiebreakers'][3],
                -totals['tiebreakers'][4]] + [-score for score in totals['tiebreakers'][5]]
            )

        return team_totals
