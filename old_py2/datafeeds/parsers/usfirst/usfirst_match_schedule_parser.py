import json
import logging

from bs4 import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstMatchScheduleParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse the table that contains the match schedule
        """
        soup = BeautifulSoup(html)

        tables = soup.findAll('table')

        matches = self.parseMatchResultList(tables[2])

        return matches, False

    @classmethod
    def parseMatchResultList(self, table):
        matches = []
        for tr in table.findAll('tr')[2:]:
            tds = tr.findAll('td')
            if len(tds) == 8 or len(tds) == 9:
                if self._recurseUntilString(tds[1]) is not None:
                    time_string = self._recurseUntilString(tds[0])
                    red_teams = ["frc" + self._recurseUntilString(tds[-6]), "frc" + self._recurseUntilString(tds[-5]), "frc" + self._recurseUntilString(tds[-4])]
                    blue_teams = ["frc" + self._recurseUntilString(tds[-3]), "frc" + self._recurseUntilString(tds[-2]), "frc" + self._recurseUntilString(tds[-1])]

                    if 'frc0' in red_teams + blue_teams:  # some matches may have placeholer teams
                        continue

                    try:
                        elim_match_number_info = self.parseElimMatchNumberInfo(self._recurseUntilString(tds[1]))
                        if elim_match_number_info is None:
                            comp_level = "qm"
                            match_number = int(self._recurseUntilString(tds[1]))
                            set_number = 1
                        else:
                            comp_level, match_number, set_number = elim_match_number_info

                        alliances = {
                            "red": {
                                "teams": red_teams,
                                "score":-1,
                            },
                            "blue": {
                                "teams": blue_teams,
                                "score":-1,
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
    def parseElimMatchNumberInfo(self, string):
        """
        Parse out the information about an elimination match based on the
        string USFIRST provides.
        They look like "Semi 2-2"
        """
        comp_level_dict = {
            "Qtr": "qf",
            "Semi": "sf",
            "Final": "f",
        }

        # string comes in as unicode.
        string = str(string).strip()

        comp_level = comp_level_dict.get(string[:-4], None)
        if comp_level is None:
            return None

        match_number = int(string[-1:])
        set_number = int(string[-3:-2])

        return comp_level, match_number, set_number
