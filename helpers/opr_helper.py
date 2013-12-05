# Calculates OPR
# For implementation details, see
# http://www.chiefdelphi.com/forums/showpost.php?p=1129108&postcount=55

# M is 2m x n where m is # of matches and n is # of teams
# s is 2m x 1 where m is # of matches
# solve [M][x]=[s] for [x] by turning it into [A][x]=[b]

# A should end up being n x n an b should end up being n x 1
# x is OPR and should be n x 1

import numpy as np
import logging


class OprHelper(object):
    @classmethod
    def calculate_oprs(cls, matches):
        """
        Returns: a list of tuples (team, opr) where
        team: a string representing a team number (Example: "254", "254B", "1114")
        opr: a float representing the OPR for that team
        """
        n, m, parsed_matches, team_list, team_id_map = cls._parse_matches(matches)
        M = np.zeros([2 * m, n])
        s = np.zeros([2 * m, 1])

        # Constructing M and s
        for row, (teams, score) in enumerate(parsed_matches):
            for team in teams:
                M[row, team_id_map[team]] = 1
            s[row] = score

        # Calculating A and b
        A = np.dot(M.transpose(), M)
        b = np.dot(M.transpose(), s)

        # Solving A*x = b for x
        x = np.linalg.solve(A, b)
#         opr_list = x.transpose().tolist()[0]  # convert a numpy column vector into Python list

        opr_dict = {}
        for team, opr in zip(team_list, x):
            opr_dict[team] = opr[0]

        return opr_dict

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
        m = len(matches)
        return n, m, parsed_matches, team_list, team_id_map
