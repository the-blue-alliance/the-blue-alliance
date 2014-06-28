import heapq

from collections import defaultdict

from consts.event_type import EventType


class DistrictHelper(object):
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
