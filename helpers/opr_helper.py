# Calculates OPR
# For implementation details, see
# http://www.chiefdelphi.com/forums/showpost.php?p=484220&postcount=19

# M is n x n where n is # of teams
# s is n x 1 where n is # of teams
# solve [M][x]=[s] for [x]

# x is OPR and should be n x 1

import numpy as np
import logging


class OprHelper(object):
    @classmethod
    def calculate_oprs(cls, matches):
        """
        Returns: a dict where
        key: a string representing a team number (Example: "254", "254B", "1114")
        value: a float representing the OPR for that team
        """
        n, parsed_matches, team_list, team_id_map = cls._parse_matches(matches)
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
        x = np.linalg.solve(M, s)

        oprs_dict = {}
        for team, opr in zip(team_list, x):
            oprs_dict[team] = opr[0]

        return oprs_dict

    @classmethod
    def _parse_matches(cls, matches):
        """
        Returns:
        n: # of teams
        m: # of matches
        parsed_matches: list of matches as the tuple ([team, team, team], score)
        team_list: list of strings representing team numbers. Example: "254", "254B", "1114"
        team_id_map: dict that maps a team to a unique integer from 0 to n-1
        """
        team_list = set()
        parsed_matches = []
        for match in matches:
            if match.comp_level != 'qm':  # only calculate OPRs for quals matches
                continue
            alliances = match.alliances
            for alliance_color in ['red', 'blue']:
                match_team_list = []
                for team in alliances[alliance_color]['teams']:
                    team = team[3:]  # turns "frc254B" into "254B"
                    team_list.add(team)
                    match_team_list.append(team)
                parsed_matches.append((match_team_list, alliances[alliance_color]['score']))

        team_list = list(team_list)

        team_id_map = {}
        for i, team in enumerate(team_list):
            team_id_map[team] = i

        n = len(team_list)
        return n, parsed_matches, team_list, team_id_map
