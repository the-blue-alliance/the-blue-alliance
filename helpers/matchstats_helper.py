# Calculates OPR/DPR/CCWM
# For implementation details, see
# http://www.chiefdelphi.com/forums/showpost.php?p=484220&postcount=19

# M is n x n where n is # of teams
# s is n x 1 where n is # of teams
# solve [M][x]=[s] for [x]

# x is OPR and should be n x 1

from collections import defaultdict
import numpy as np

from google.appengine.api import memcache

from database import event_query
from models.event_team import EventTeam


class MatchstatsHelper(object):
    @classmethod
    def calculate_matchstats(cls, matches, year):
        parsed_matches_by_type, team_list, team_id_map = cls._parse_matches(matches, year)

        oprs_dict = cls._calculate_stat(parsed_matches_by_type['opr'], team_list, team_id_map)
        xoprs_dict = cls._calculate_stat(parsed_matches_by_type['xopr'], team_list, team_id_map)
        dprs_dict = cls._calculate_stat(parsed_matches_by_type['dpr'], team_list, team_id_map)
        ccwms_dict = cls._calculate_stat(parsed_matches_by_type['ccwm'], team_list, team_id_map)

        stats = {'oprs': oprs_dict, 'dprs': dprs_dict, 'ccwms': ccwms_dict, 'xoprs': xoprs_dict}
        if year == 2016:
            stats['year_specific'] = {}
            stats['year_specific']['bouldersOPR'] = cls._calculate_stat(parsed_matches_by_type['bouldersOPR'], team_list, team_id_map)
            stats['year_specific']['breachRate'] = cls._calculate_rate(parsed_matches_by_type['breachRate'])

        init_oprs = xoprs_dict
        for _ in range(2):  # 2 iterations of ixOPR seems to work well
            parsed_matches_by_type, team_list, team_id_map = cls._parse_matches(matches, year, init_oprs)
            ixoprs_dict = cls._calculate_stat(parsed_matches_by_type['xopr'], team_list, team_id_map)
            init_oprs = cls._calculate_stat(parsed_matches_by_type['xopr'], team_list, team_id_map)
        stats['ixoprs']= ixoprs_dict

        return stats

    @classmethod
    def _calculate_rate(cls, parsed_matches):
        totals = defaultdict(int)
        successes = defaultdict(int)
        for teams, value in parsed_matches:
            for team in teams:
                totals[team] += 1
                if value:
                    successes[team] += 1

        stat = {}
        for team, total in totals.items():
            stat[team] = float(successes[team]) / total

        return stat

    @classmethod
    def _calculate_stat(cls, parsed_matches, team_list, team_id_map):
        """
        Returns: a dict where
        key: a string representing a team number (Example: "254", "254B", "1114")
        value: a float representing the stat (OPR/DPR/CCWM) for that team
        """
        n = len(team_list)
        M = np.zeros([n, n])
        s = np.zeros([n, 1])

        # Constructing M and s
        for teams, score in parsed_matches:
            for team1 in teams:
                team1_id = team_id_map[team1]
                for team2 in teams:
                    M[team1_id, team_id_map[team2]] += 1
                s[team1_id] += score

        # Solving M*x = s for x
        try:
            # x = np.linalg.solve(M, s)
            x = np.dot(np.linalg.pinv(M), s)  # Similar to above, but more numerically stable
        except (np.linalg.LinAlgError, ValueError):
            return {}

        stat_dict = {}
        for team, stat in zip(team_list, x):
            stat_dict[team] = stat[0]

        return stat_dict

    @classmethod
    def get_last_event_stats(cls, team_list, event_key, stat):
        year = int(event_key.id()[:4])
        cur_event = event_key.get()

        # Check cache for stored OPRs
        cache_key = '{}:last_event_stats'.format(event_key.id())
        last_event_stats = memcache.get(cache_key)
        if last_event_stats is None:
            last_event_stats = {}

        # Make necessary queries for missing stats
        futures = []
        for team in team_list:
            if team not in last_event_stats:
                events_future = event_query.TeamYearEventsQuery('frc{}'.format(team), year).fetch_async()
                futures.append((team, events_future))

        # Add missing stats to last_event_stats
        for team, events_future in futures:
            events = events_future.get_result()

            # Find last event before current event
            last_event = None
            last_event_start = None
            for event in events:
                if event.start_date < cur_event.start_date:
                    if last_event is None or event.start_date > last_event_start:
                        last_event = event
                        last_event_start = event.start_date

            if last_event is not None and stat in last_event.matchstats and team in last_event.matchstats[stat]:
                last_event_opr = last_event.matchstats[stat][team]
                last_event_stats[team] = last_event_opr

        memcache.set(cache_key, last_event_stats, 60*60*24)
        return last_event_stats

    @classmethod
    def _parse_matches(cls, matches, year, init_oprs=None):
        """
        Returns:
        parsed_matches_by_type: list of matches as the tuple ([team, team, team], <score/opposingscore/scoremargin>) for each key ('opr', 'dpr', 'ccwm')
        team_list: list of strings representing team numbers. Example: "254", "254B", "1114"
        team_id_map: dict that maps a team to a unique integer from 0 to n-1
        """
        team_list = set()
        parsed_matches_by_type = {
            'opr': [],
            'xopr': [],
            'dpr': [],
            'ccwm': [],
        }
        # Add year specific OPRs
        if year == 2016:
            parsed_matches_by_type['bouldersOPR'] = []
            parsed_matches_by_type['breachRate'] = []

        # Build team list
        for match in matches:
            if match.comp_level != 'qm':  # only calculate OPRs for played quals matches
                continue
            alliances = match.alliances
            for alliance_color in ['red', 'blue']:
                for team in alliances[alliance_color]['teams']:
                    team_list.add(team[3:])  # turns "frc254B" into "254B"

        # Load last OPR data
        if init_oprs is None:
            last_event_oprs = cls.get_last_event_stats(team_list, matches[0].event, 'oprs')
        else:
            last_event_oprs = {}
            for team, xopr in init_oprs.items():
                last_event_oprs[team] = xopr

        for match in matches:
            if match.comp_level != 'qm':  # only calculate OPRs for played quals matches
                continue
            alliances = match.alliances
            for alliance_color, opposing_color in zip(['red', 'blue'], ['blue', 'red']):
                match_team_list = []
                predicted_score = 0
                for team in alliances[alliance_color]['teams']:
                    team = team[3:]  # turns "frc254B" into "254B"
                    match_team_list.append(team)
                    predicted_score += last_event_oprs.get(team, 0)  # TODO use something other than 0

                if match.has_been_played:  # only calculate OPRs for played matches
                    alliance_score = int(alliances[alliance_color]['score'])
                    opposing_score = int(alliances[opposing_color]['score'])
                    parsed_matches_by_type['opr'].append((match_team_list, alliance_score))
                    parsed_matches_by_type['xopr'].append((match_team_list, alliance_score))
                    parsed_matches_by_type['dpr'].append((match_team_list, opposing_score))
                    parsed_matches_by_type['ccwm'].append((match_team_list, alliance_score - opposing_score))

                    if year == 2016 and match.score_breakdown and alliance_color in match.score_breakdown:
                        parsed_matches_by_type['bouldersOPR'].append((match_team_list,
                            match.score_breakdown[alliance_color].get('autoBouldersLow', 0) +
                            match.score_breakdown[alliance_color].get('autoBouldersHigh', 0) +
                            match.score_breakdown[alliance_color].get('teleopBouldersLow', 0) +
                            match.score_breakdown[alliance_color].get('teleopBouldersHigh', 0)))
                        parsed_matches_by_type['breachRate'].append((match_team_list, match.score_breakdown[alliance_color].get('teleopDefensesBreached', False)))
                else:
                    parsed_matches_by_type['xopr'].append((match_team_list, predicted_score))

        team_list = list(team_list)

        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        return parsed_matches_by_type, team_list, team_id_map
