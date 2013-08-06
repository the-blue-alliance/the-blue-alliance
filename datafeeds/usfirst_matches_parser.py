import json
import logging

from BeautifulSoup import BeautifulSoup

from datafeeds.parser_base import ParserBase


class UsfirstMatchesParser(ParserBase):
    @classmethod
    def parse(self, html):
        """
        Parse the table that contains qualification match results.
        """
        matches = list()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)

        tables = soup.findAll('table')

        matches.extend(self.parseQualMatchResultList(tables[2]))
        matches.extend(self.parseElimMatchResultList(tables[2]))
        matches.extend(self.parseElimMatchResultList(tables[3]))

        return matches, False

    @classmethod
    def parseQualMatchResultList(self, table):
        matches = list()
        for tr in table.findAll('tr')[2:]:
            tds = tr.findAll('td')
            if len(tds) == 10:
                if self._recurseUntilString(tds[1]) is not None:
                    time_string = self._recurseUntilString(tds[0])
                    red_teams = ["frc" + self._recurseUntilString(tds[2]), "frc" + self._recurseUntilString(tds[3]), "frc" + self._recurseUntilString(tds[4])]
                    blue_teams = ["frc" + self._recurseUntilString(tds[5]), "frc" + self._recurseUntilString(tds[6]), "frc" + self._recurseUntilString(tds[7])]

                    try:
                        if self._recurseUntilString(tds[8]) == None:
                            red_score = -1
                        else:
                            red_score = int(self._recurseUntilString(tds[8]))

                        if self._recurseUntilString(tds[9]) == None:
                            blue_score = -1
                        else:
                            blue_score = int(self._recurseUntilString(tds[9]))

                        match_number = int(self._recurseUntilString(tds[1]))

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
                            "comp_level": "qm",
                            "match_number": match_number,
                            "set_number": 1,
                            "team_key_names": red_teams + blue_teams,
                            "time_string": time_string
                            })

                    except Exception, detail:
                        logging.info('Match Parse Failed: ' + str(detail))

        return matches

    @classmethod
    def parseElimMatchResultList(self, table):
        """
        Parse the table that contains elimination match results.
        """
        matches = list()
        for tr in table.findAll('tr')[2:]:
            tds = tr.findAll('td')
            if len(tds) == 11:
                if self._recurseUntilString(tds[1]) is not None:
                    time_string = self._recurseUntilString(tds[0])
                    red_teams = ["frc" + self._recurseUntilString(tds[3]), "frc" + self._recurseUntilString(tds[4]), "frc" + self._recurseUntilString(tds[5])]
                    blue_teams = ["frc" + self._recurseUntilString(tds[6]), "frc" + self._recurseUntilString(tds[7]), "frc" + self._recurseUntilString(tds[8])]

                    try:
                        if self._recurseUntilString(tds[9]) == None:
                            red_score = -1
                        else:
                            red_score = int(self._recurseUntilString(tds[9]))

                        if self._recurseUntilString(tds[10]) == None:
                            blue_score = -1
                        else:
                            blue_score = int(self._recurseUntilString(tds[10]))

                        match_number_info = self.parseElimMatchNumberInfo(self._recurseUntilString(tds[1]))

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

                        # Don't write down uncompleted elimination matches
                        if (red_score > -1 and blue_score > -1):
                            matches.append({
                                "alliances_json": json.dumps(alliances),
                                "comp_level": match_number_info["comp_level"],
                                "match_number": match_number_info["match_number"],
                                "set_number": match_number_info["set_number"],
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

        match_number = int(string[-1:])
        set_number = int(string[-3:-2])
        comp_level = comp_level_dict[string[:-4]]

        return {
            "match_number": match_number,
            "set_number": set_number,
            "comp_level": comp_level,
        }
