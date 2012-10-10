import json
import logging
import csv
import StringIO
import re

from datafeeds.parser_base import ParserBase

class OffseasonMatchesParser(ParserBase):
    @classmethod
    def parse(self, data):
        """
        Parse CSV that contains match results.
        Format is as follows:
        match_id, red1, red2, red3, blue1, blue2, blue3, red score, blue score
        
        Example formats of match_id:
        qm1, sf2-1, f1-1
        """
        matches = list()
        
        csv_data = list(csv.reader(StringIO.StringIO(data), delimiter=',', skipinitialspace=True))
        for row in csv_data:
            matches.append(self.parseCSVMatch(row))

        return matches
    
    @classmethod
    def parseCSVMatch(self, row):
        match_id, red_1, red_2, red_3, blue_1, blue_2, blue_3, red_score, blue_score = row
        
        red_teams = ["frc" + red_1, "frc" + red_2, "frc" + red_3]
        blue_teams = ["frc" + blue_1, "frc" + blue_2, "frc" + blue_3]
        
        if not red_score:
            red_score = -1
        else:
            red_score = int(red_score)
            
        if not blue_score:
            blue_score = -1
        else:
            blue_score = int(blue_score)
            
        comp_level, match_number, set_number = self.parseMatchNumberInfo(match_id)
            
        alliances = {"red": {"teams": red_teams,
                             "score": red_score},
                     "blue": {"teams": blue_teams,
                              "score": blue_score}}
        
        match = {"alliances_json": json.dumps(alliances),
                 "comp_level": comp_level,
                 "match_number": match_number,
                 "set_number": set_number,
                 "team_key_names": red_teams + blue_teams}
                            
        return match
    
    
    @classmethod
    def parseMatchNumberInfo(self, string):
        string = string.strip()
        pattern = re.compile('[0123456789-]')
        comp_level = pattern.sub('', string)
        
        MATCH_PARSE_STYLE = {'qm': self.parseQualMatchNumberInfo,
                             'qf': self.parseElimMatchNumberInfo,
                             'sf': self.parseElimMatchNumberInfo,
                             'f': self.parseElimMatchNumberInfo,}

        match_number, set_number = MATCH_PARSE_STYLE[comp_level](string)
        return comp_level, match_number, set_number
    
    @classmethod
    def parseQualMatchNumberInfo(self, string):
        match_number = int(string[-1:])
        return match_number, 1
    
    @classmethod
    def parseElimMatchNumberInfo(self, string):
        match_number = int(string[-1:])
        set_number = int(string[-3:-2])
        return match_number, set_number
