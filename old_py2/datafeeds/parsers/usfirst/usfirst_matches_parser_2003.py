import json
import re
import logging

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstMatchesParser2003(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse the table that contains qualification match results.
        Note that 2002 match tables aren't consistently formatted, and this
        parser takes that into account.
        """
        soup = BeautifulSoup(html)

        match_table = soup.findAll('table')[0]
        matches = self.parseMatchResultList(match_table)

        return matches, False

    @classmethod
    def parseMatchResultList(self, table):
        matches = []
        mid_match = False  # Matches are split across rows. This keeps track of whether or not we are parsing the same match.
        ignore_match = False  # Parsing failed. Ignore this match
        mid_match_comp_level = None
        mid_match_number = None
        mid_match_set_number = None
        mid_match_teams = []  # Teams for the current match, if mid_match. If not mid match, this should be empty.
        mid_match_scores = []  # Scores for the current match, if mid_match. If not mid match, this should be empty.
        for tr in table.findAll('tr')[2:]:  # skip table headers
            tds = tr.findAll('td')
            match_name = self._recurseUntilString(tds[0])

            # Start of a new match. Combine info and reset mid_match info.
            if mid_match and (match_name is not None or len(tds) == 1):
                if not ignore_match:
                    if len(mid_match_teams) == len(mid_match_scores):
                        blue_teams = mid_match_teams[:len(mid_match_teams) / 2]
                        red_teams = mid_match_teams[len(mid_match_teams) / 2:]
                        blue_score = mid_match_scores[0]
                        red_score = mid_match_scores[len(mid_match_scores) / 2]
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
                match_name_lower = match_name.lower()
                if 'elim' in match_name_lower:
                    # looks like: "Elim Finals.1" or or "Elim QF1.2"
                    if 'finals' in match_name_lower:
                        mid_match_comp_level = 'f'
                        mid_match_set_number = 1
                        try:
                            mid_match_number = int(re.findall(r'\d+', match_name)[0])
                        except:
                            logging.warning("Finals match number parse for '%s' failed!" % match_name)
                            ignore_match = True
                            continue
                    else:
                        if 'qf' in match_name_lower:
                            mid_match_comp_level = 'qf'
                        elif 'sf' in match_name_lower:
                            mid_match_comp_level = 'sf'
                        else:
                            logging.warning("Could not extract comp level from: {}".format(match_name))
                            ignore_match = True
                            continue

                        try:
                            prefix, suffix = match_name_lower.split('.')
                            mid_match_set_number = int(prefix[-1])
                            mid_match_number = int(suffix[0])
                        except:
                            logging.warning("Could not extract match set and number from: {}".format(match_name))
                            ignore_match = True
                            continue
                else:
                    mid_match_comp_level = 'qm'
                    mid_match_set_number = 1
                    try:
                        mid_match_number = int(re.findall(r'\d+', match_name)[0])
                    except:
                        logging.warning("Qual match number parse for '%s' failed!" % match_name)
                        ignore_match = True
                        continue
            else:
                team_col = self._recurseUntilString(tds[2])
                try:
                    team_key = 'frc{}'.format(int(re.findall(r'\d+', team_col)[0]))
                except:
                    logging.warning("Team number parse for '%s' failed!" % team_col)
                    ignore_match = True
                    continue

                score_col = self._recurseUntilString(tds[3])
                try:
                    match_score = int(re.findall(r'\d+', score_col)[0])
                    if match_score is None:
                        match_score = -1
                except:
                    logging.warning("Score parse for '%s' failed!" % score_col)
                    ignore_match = True
                    continue

                mid_match_teams.append(team_key)
                mid_match_scores.append(match_score)

        return matches
