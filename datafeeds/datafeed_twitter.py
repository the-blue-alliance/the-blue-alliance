import logging

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.offseason_matches_parser import OffseasonMatchesParser

class DatafeedTwitter(DatafeedBase):
    def __init__(self, *args, **kw):
        super(DatafeedTwitter, self).__init__(*args, **kw)

    def getMatches(self, event, url):
        matches = self.parse(url, OffseasonMatchesParser)
        logging.info(matches)

        return [Match(
            id = Match.getKeyName(
                event, 
                match.get("comp_level", None), 
                match.get("set_number", 0), 
                match.get("match_number", 0)),
            event = event.key,
            game = Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
            set_number = match.get("set_number", 0),
            match_number = match.get("match_number", 0),
            comp_level = match.get("comp_level", None),
            team_key_names = match.get("team_key_names", None),
            alliances_json = match.get("alliances_json", None)
            )
            for match in matches]
