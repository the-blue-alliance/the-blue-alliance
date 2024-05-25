import json
import re
import logging

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstMatchesParser2002(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse the table that contains qualification match results.
        Note that 2002 match tables aren't consistently formatted, and this
        parser takes that into account.
        """
        soup = BeautifulSoup(html)

        match_table = soup.findAll('table')[5].findAll('table')[0].findAll('table')[1]
        matches = self.parseMatchResultList(match_table)

        return matches, False

    @classmethod
    def parseMatchResultList(self, table):
        """
        Makes use of the assumption that all qual matches are before elim
        matches in the table.
        """
        matches = []
        mid_match = False  # Matches are split across rows. This keeps track of whether or not we are parsing the same match.
        ignore_match = False  # Parsing failed. Ignore this match
        mid_match_comp_level = None
        mid_match_number = None
        mid_match_set_number = None
        mid_match_teams = []  # Teams for the current match, if mid_match. If not mid match, this should be empty.
        mid_match_scores = []  # Scores for the current match, if mid_match. If not mid match, this should be empty.
        elim_match_counter = {}  # Keeps track of the last set number. Keys are like "qf1" and values are like "2"
        for tr in table.findAll('tr')[1:]:  # skip table header
            tds = tr.findAll('td')
            col1 = self._recurseUntilString(tds[0])

            # End of a match or start of a new match. Combine info and reset mid_match info.
            if mid_match and (col1 is None or 'match' in col1.lower()):
                if not ignore_match:
                    if len(mid_match_teams) == len(mid_match_scores):
                        red_teams = mid_match_teams[:len(mid_match_teams) / 2]
                        blue_teams = mid_match_teams[len(mid_match_teams) / 2:]
                        red_score = mid_match_scores[0]
                        blue_score = mid_match_scores[len(mid_match_scores) / 2]
                        alliances = {"red": {
                                        "teams": red_teams,
                                        "score": red_score
                                    },
                                    "blue": {
                                        "teams": blue_teams,
                                        "score": blue_score
                                    }
                        }
                        matches.append({"alliances_json": json.dumps(alliances),
                                        "comp_level": mid_match_comp_level,
                                        "match_number": mid_match_number,
                                        "set_number": mid_match_set_number,
                                        "team_key_names": red_teams + blue_teams,
                        })
                    else:
                        logging.warning("Lengths of mid_match_teams ({}) and mid_match_scores ({}) aren't the same!".format(mid_match_teams, mid_match_scores))

                mid_match = False
                ignore_match = False
                mid_match_comp_level = None
                mid_match_number = None
                mid_match_set_number = None
                mid_match_teams = []
                mid_match_scores = []
                continue

            if not mid_match:
                mid_match = True
                try:
                    match_or_set_number = int(re.findall(r'\d+', col1)[0])
                except:
                    logging.warning("Match/Set number parse for '{}' failed!".format(col1))
                    ignore_match = True
                    continue

                col1_lower = col1.lower()
                if (('final' in col1_lower) or ('quarter' in col1_lower) or
                   ('semi' in col1_lower) or ('champ' in col1_lower)):

                    if 'quarter' in col1_lower:
                        mid_match_comp_level = 'qf'
                    elif 'semi' in col1_lower:
                        mid_match_comp_level = 'sf'
                    else:
                        mid_match_comp_level = 'f'

                    match_counter_key = '{}{}'.format(mid_match_comp_level, match_or_set_number)
                    if match_counter_key in elim_match_counter:
                        elim_match_counter[match_counter_key] += 1
                    else:
                        elim_match_counter[match_counter_key] = 1
                    mid_match_set_number = match_or_set_number
                    mid_match_number = elim_match_counter[match_counter_key]
                else:
                    mid_match_comp_level = 'qm'
                    mid_match_set_number = 1
                    mid_match_number = match_or_set_number

            else:
                try:
                    team_key = 'frc{}'.format(int(re.findall(r'\d+', col1)[0]))
                except:
                    logging.warning("Team number parse for '{}' failed!".format(col1))
                    ignore_match = True
                    continue

                score_col = self._recurseUntilString(tds[1])
                try:
                    match_score = int(re.findall(r'\d+', score_col)[0])
                    if match_score is None:
                        match_score = -1
                except:
                    logging.warning("Score parse for '{}' failed!".format(score_col))
                    ignore_match = True
                    continue

                mid_match_teams.append(team_key)
                mid_match_scores.append(match_score)

        return matches
