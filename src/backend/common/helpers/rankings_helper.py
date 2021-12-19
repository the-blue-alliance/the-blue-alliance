from typing import List, Optional

from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.models.event_details import EventDetails
from backend.common.models.event_ranking import EventRanking
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey, Year
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class RankingsHelper:
    NO_RECORD_YEARS = {2010, 2015, 2021}

    QUAL_AVERAGE_YEARS = {2015}

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
        record: Optional[WLTRecord] = None
        if year not in cls.NO_RECORD_YEARS:
            record = {
                "wins": int(wins),
                "losses": int(losses),
                "ties": int(ties),
            }

        if year not in cls.QUAL_AVERAGE_YEARS:
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
        return SORT_ORDER_INFO.get(event_details.game_year)
