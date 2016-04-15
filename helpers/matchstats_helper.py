# Calculates OPR/DPR/CCWM
# For implementation details, see
# http://www.chiefdelphi.com/forums/showpost.php?p=484220&postcount=19

# M is n x n where n is # of teams
# s is n x 1 where n is # of teams
# solve [M][x]=[s] for [x]

# x is OPR and should be n x 1

import numpy as np

from google.appengine.api import memcache

from database import event_query
from models.event_team import EventTeam


class MatchstatsHelper(object):
    @classmethod
    def calculate_matchstats(cls, matches):
        parsed_matches_by_type, team_list, team_id_map = cls._parse_matches(matches)

        oprs_dict = cls._calculate_stat(parsed_matches_by_type['opr'], team_list, team_id_map)
        dprs_dict = cls._calculate_stat(parsed_matches_by_type['dpr'], team_list, team_id_map)
        ccwms_dict = cls._calculate_stat(parsed_matches_by_type['ccwm'], team_list, team_id_map)
        xoprs_dict = cls._calculate_xoprs(oprs_dict, matches, len(team_list))

        return {'oprs': oprs_dict, 'dprs': dprs_dict, 'ccwms': ccwms_dict, 'xoprs': xoprs_dict}

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
    def _calculate_xoprs(cls, oprs_dict, matches, num_teams):
        """
        Calculate cross-event adjusted OPR
        xopr = a * previous_event_opr + (1-a) * normalOPR
        a = max(1 - num_played_matches/(num_teams/2), 0)
        """
        num_played = 0
        for match in matches:
            if not match.has_been_played or match.comp_level != 'qm':  # only calculate xOPRs for played quals matches
                continue
            num_played += 1

        a = max(1 - 2.0 * num_played / num_teams, 0)
        if a == 0:
            return oprs_dict

        year = matches[0].year
        event_key = matches[0].event
        cur_event = event_key.get()

        # Check cache for stored OPRs
        cache_key = '{}:last_event_oprs'.format(event_key.id())
        last_event_oprs = memcache.get(cache_key)
        if last_event_oprs is None:
            last_event_oprs = {}

        # Make necessary queries for missing OPRs
        futures = []
        for team, opr in oprs_dict.items():
            if team not in last_event_oprs:
                events_future = event_query.TeamYearEventsQuery('frc{}'.format(team), year).fetch_async()
                futures.append((team, events_future))

        # Add missing OPRs to last_event_oprs
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

            last_event_opr = last_event.matchstats['oprs'].get(team, 0)
            last_event_oprs[team] = last_event_opr

        xoprs_dict = {}
        for team, opr in oprs_dict.items():
            last_event_opr = last_event_oprs[team]
            xoprs_dict[team] = a * last_event_opr + (1-a) * opr

        memcache.set(cache_key, last_event_oprs, 60*60*24)

        return xoprs_dict

    @classmethod
    def _parse_matches(cls, matches):
        """
        Returns:
        parsed_matches_by_type: list of matches as the tuple ([team, team, team], <score/opposingscore/scoremargin>) for each key ('opr', 'dpr', 'ccwm')
        team_list: list of strings representing team numbers. Example: "254", "254B", "1114"
        team_id_map: dict that maps a team to a unique integer from 0 to n-1
        """
        team_list = set()
        parsed_matches_by_type = {
            'opr': [],
            'dpr': [],
            'ccwm': [],
        }
        for match in matches:
            if match.comp_level != 'qm':  # only calculate OPRs for played quals matches
                continue
            alliances = match.alliances
            for alliance_color, opposing_color in zip(['red', 'blue'], ['blue', 'red']):
                match_team_list = []
                for team in alliances[alliance_color]['teams']:
                    team = team[3:]  # turns "frc254B" into "254B"
                    team_list.add(team)  # Needed for xoprs
                    match_team_list.append(team)

                if match.has_been_played:  # only calculate OPRs for played matches
                    alliance_score = int(alliances[alliance_color]['score'])
                    opposing_score = int(alliances[opposing_color]['score'])
                    parsed_matches_by_type['opr'].append((match_team_list, alliance_score))
                    parsed_matches_by_type['dpr'].append((match_team_list, opposing_score))
                    parsed_matches_by_type['ccwm'].append((match_team_list, alliance_score - opposing_score))

        team_list = list(team_list)

        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        return parsed_matches_by_type, team_list, team_id_map
