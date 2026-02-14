from backend.common.frc_api.types import (
    EventRankingListModelV2,
    EventRankingTeamModelV2,
)
from backend.common.helpers.rankings_helper import RankingsHelper
from backend.common.models.event_ranking import EventRanking
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class FMSAPIEventRankingsParser(
    ParserBase[EventRankingListModelV2, list[EventRanking]]
):
    def __init__(self, year: int) -> None:
        self.year = year

    def parse(self, response: EventRankingListModelV2) -> list[EventRanking]:
        rankings = []

        api_rankings: list[EventRankingTeamModelV2] = response["Rankings"] or []
        for team in api_rankings:
            sort_orders = []

            count = 1
            order_name = "sortOrder{}".format(count)
            while order_name in team:
                sort_orders.append(team[order_name])  # pyre-ignore[26]
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

        return rankings
