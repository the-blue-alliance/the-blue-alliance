import json
import logging

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstMatchesParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse the table that contains match results.
        """
        matches = []
        soup = BeautifulSoup(html)

        tables = soup.findAll('table')

        matches.extend(self.parseMatchResultList(tables[2]))
        matches.extend(self.parseMatchResultList(tables[3]))

        return matches, False

    @classmethod
    def parseMatchResultList(self, table):
        matches = list()
        for tr in table.findAll('tr')[2:]:
            tds = tr.findAll('td')
            if len(tds) == 10 or len(tds) == 11:  # qual has 10, elim has 11
                if self._recurseUntilString(tds[1]) is not None:
                    time_string = self._recurseUntilString(tds[0])
                    red_teams = ["frc" + self._recurseUntilString(tds[-8]),
                                 "frc" + self._recurseUntilString(tds[-7]),
                                 "frc" + self._recurseUntilString(tds[-6])]
                    blue_teams = ["frc" + self._recurseUntilString(tds[-5]),
                                  "frc" + self._recurseUntilString(tds[-4]),
                                  "frc" + self._recurseUntilString(tds[-3])]

                    try:
                        if self._recurseUntilString(tds[-2]) is None:
                            red_score = -1
                        else:
                            red_score = int(self._recurseUntilString(tds[-2]))

                        if self._recurseUntilString(tds[-1]) is None:
                            blue_score = -1
                        else:
                            blue_score = int(self._recurseUntilString(tds[-1]))

                        comp_level, match_number, set_number = self.parseMatchNumberInfo(self._recurseUntilString(tds[1]))

                        alliances = {
                            "red": {
                                "teams": red_teams,
                                "score": red_score
                            },
                            "blue": {
                                "teams": blue_teams,
                                "score": blue_score
                            }
                        }

                        matches.append({
                            "alliances_json": json.dumps(alliances),
                            "comp_level": comp_level,
                            "match_number": match_number,
                            "set_number": set_number,
                            "team_key_names": red_teams + blue_teams,
                            "time_string": time_string
                            })

                    except Exception, detail:
                        logging.info('Match Parse Failed: ' + str(detail))

        return matches

    @classmethod
    def parseMatchNumberInfo(self, string):
        """
        Parse out the information about an qual or elim match based on the
        string USFIRST provides.
        They look like "34", "Semi 2-2", or "Final 1-1"
        """
        comp_level_dict = {
            "Qtr": "qf",
            "Semi": "sf",
            "Final": "f",
        }

        # string comes in as unicode.
        string = str(string).strip()
        comp_level = comp_level_dict.get(string[:-4], "qm")
        if comp_level == 'qm':
            match_number = int(string)
            set_number = 1
        else:
            match_number = int(string[-1:])
            set_number = int(string[-3:-2])

        return comp_level, match_number, set_number
