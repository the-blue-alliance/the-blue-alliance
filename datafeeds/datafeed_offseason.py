import logging

from datafeeds.datafeed_base import DatafeedBase
from datafeeds.offseason_matches_parser import OffseasonMatchesParser

from models.match import Match


class DatafeedOffseason(DatafeedBase):
    def __init__(self, *args, **kw):
        super(DatafeedOffseason, self).__init__(*args, **kw)

    def getMatches(self, event, url):
        matches, _ = self.parse(url, OffseasonMatchesParser)
        logging.info(matches)

        return [
            Match(
                id=Match.renderKeyName(event.key.id(),
                                       match.get("comp_level", None),
                                       match.get("set_number", 0),
                                       match.get("match_number", 0)),
                event=event.key,
                year=event.year,
                set_number=match.get("set_number", 0),
                match_number=match.get("match_number", 0),
                comp_level=match.get("comp_level", None),
                team_key_names=match.get("team_key_names", None),
                alliances_json=match.get("alliances_json", None))
            for match in matches
        ]
