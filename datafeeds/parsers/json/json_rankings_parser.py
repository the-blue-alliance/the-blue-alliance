import json
import re

from datafeeds.parser_base import ParserInputException, ParserBase


class JSONRankingsParser(ParserBase):
    @classmethod
    def parse(self, rankings_json):
        """
        Parse JSON that contains a dict of:
        breakdowns: List of ranking breakdowns, such as "Wins", "Qual Avg", "QS", "Auton", "Teleop", etc. Breakdowns will be shown in the order given.
        rankings: List of ranking dicts

        Ranking dict format:
        team_key: String corresponding to a particular team in the format "frcXXX"
        rank: Integer rank of the particular team
        played: Integer of the number of non-surrogate matches played
        dqs: Integer of the number of non-surrogate DQed matches
        breakdown: Dict where the key is a breakdown and the value is its value
        """
        try:
            data = json.loads(rankings_json)
        except:
            raise ParserInputException("Invalid JSON. Please check input.")

        if type(data) is not dict:
            raise ParserInputException("Data must be a dict.")
        if 'breakdowns' not in data or type(data['breakdowns']) is not list:
            raise ParserInputException("Data must have a list 'breakdowns'")
        if 'rankings' not in data or type(data['rankings']) is not list:
            raise ParserInputException("Data must have a list 'rankings'")

        # Account for wins/losses/ties to be present and show them as Record (W-L-T)
        post_breakdowns = ['DQ', 'Played']
        has_record = False
        if "wins" in data["breakdowns"] and "losses" in data["breakdowns"] and "ties" in data["breakdowns"]:
            post_breakdowns.insert(0, 'Record (W-L-T)')
            has_record = True

            # remove wlt from breakdown list so they're not added twice
            data["breakdowns"].remove("wins")
            data["breakdowns"].remove("losses")
            data["breakdowns"].remove("ties")

        rankings = [['Rank', 'Team'] + data['breakdowns'] + post_breakdowns]
        for ranking in data['rankings']:
            if type(ranking) is not dict:
                raise ParserInputException("Ranking must be a dict.")
            if 'team_key' not in ranking or not re.match(r'frc\d+', str(ranking['team_key'])):
                raise ParserInputException("Ranking must have a 'team_key' that follows the format 'frcXXX'")
            for attr in ['rank', 'played', 'dqs']:
                if attr not in ranking or type(ranking[attr]) is not int:
                    raise ParserInputException("Ranking must have a integer '{}'".format(attr))

            row = [ranking['rank'], ranking['team_key'][3:]]
            for b in data['breakdowns']:
                row.append(ranking.get(b, '--'))

            # Special case for when wlt passed
            if has_record:
                row.extend(['{}-{}-{}'.format(ranking['wins'], ranking['losses'], ranking['ties']), ranking['dqs'], ranking['played']])
            else:
                row.extend([ranking['dqs'], ranking['played']])
            rankings.append(row)

        return rankings
