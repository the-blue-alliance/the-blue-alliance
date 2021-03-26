from typing import Any, Dict, List, Optional

from backend.common.datafeeds.parsers.json.parser_json import ParserJSON
from backend.common.helpers.rankings_helper import RankingsHelper
from backend.common.models.event_ranking import EventRanking


class FMSAPIEventRankingsParser(ParserJSON[List[EventRanking]]):
    def __init__(self, year: int) -> None:
        self.year = year

    def parse(self, response: Dict[str, Any]) -> Optional[List[EventRanking]]:
        rankings = []

        for team in response["Rankings"]:
            sort_orders = []

            count = 1
            order_name = "sortOrder{}".format(count)
            while order_name in team:
                sort_orders.append(team[order_name])
                count += 1
                order_name = "sortOrder{}".format(count)

            rankings.append(
                RankingsHelper.build_ranking(
                    self.year,
                    team["rank"],
                    "frc{}".format(team["teamNumber"]),
                    team["wins"],
                    team["losses"],
                    team["ties"],
                    team["qualAverage"],
                    team["matchesPlayed"],
                    team["dq"],
                    sort_orders,
                )
            )

        return rankings if rankings else None
