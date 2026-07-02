from typing import List, Optional

from backend.common.game_specific.registry import get_game
from backend.common.models.event_details import EventDetails
from backend.common.models.event_ranking import EventRanking
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey, Year
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class RankingsHelper:
    @classmethod
    def build_ranking(
        cls,
        year: Year,
        rank: int,
        team_key: TeamKey,
        wins: int,
        losses: int,
        ties: int,
        qual_average: Optional[float],
        matches_played: int,
        dq: int,
        sort_orders: List[float],
    ) -> EventRanking:
        game = get_game(year)
        record: Optional[WLTRecord] = None
        if game.record_in_rankings():
            record = {
                "wins": int(wins),
                "losses": int(losses),
                "ties": int(ties),
            }

        if not game.qual_average_in_rankings():
            qual_average = None

        sort_orders_sanitized = []
        for so in sort_orders:
            try:
                sort_orders_sanitized.append(float(so))
            except Exception:
                sort_orders_sanitized.append(0.0)

        return {
            "rank": int(rank),
            "team_key": team_key,
            "record": record,  # None if record doesn't affect rank (e.g. 2010, 2015)
            "qual_average": qual_average,  # None if qual_average doesn't affect rank (all years except 2015)
            "matches_played": int(matches_played),
            "dq": int(dq),
            "sort_orders": sort_orders_sanitized,
        }

    @classmethod
    def get_sort_order_info(
        cls, event_details: EventDetails
    ) -> Optional[List[RankingSortOrderInfo]]:
        return get_game(event_details.game_year).ranking_sort_order_info()
