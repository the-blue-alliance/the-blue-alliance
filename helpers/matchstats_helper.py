# Calculates OPR/DPR/CCWM
# For implementation details, see
# http://www.chiefdelphi.com/forums/showpost.php?p=484220&postcount=19

# M is n x n where n is # of teams
# s is n x 1 where n is # of teams
# solve [M][x]=[s] for [x]

# x is OPR and should be n x 1

import numpy as np
import logging


class MatchstatsHelper(object):
    @classmethod
    def calculate_matchstats(cls, matches):
        parsed_matches_by_type, team_list, team_id_map = cls._parse_matches(matches)

        oprs_dict = cls._calculate_stat(parsed_matches_by_type['opr'], team_list, team_id_map)
        dprs_dict = cls._calculate_stat(parsed_matches_by_type['dpr'], team_list, team_id_map)
        ccwms_dict = cls._calculate_stat(parsed_matches_by_type['ccwm'], team_list, team_id_map)

        return {'oprs': oprs_dict, 'dprs': dprs_dict, 'ccwms': ccwms_dict}

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
            x = np.linalg.solve(M, s)
        except (np.linalg.LinAlgError, ValueError):
            return {}

        stat_dict = {}
        for team, stat in zip(team_list, x):
            stat_dict[team] = stat[0]

        return stat_dict

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
            if not match.has_been_played or match.comp_level != 'qm':  # only calculate OPRs for played quals matches
                continue
            alliances = match.alliances
            for alliance_color, opposing_color in zip(['red', 'blue'], ['blue', 'red']):
                match_team_list = []
                for team in alliances[alliance_color]['teams']:
                    team = team[3:]  # turns "frc254B" into "254B"
                    team_list.add(team)
                    match_team_list.append(team)

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
