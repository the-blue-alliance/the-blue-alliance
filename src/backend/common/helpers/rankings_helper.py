from typing import List, Optional

from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.models.event_details import EventDetails
from backend.common.models.event_ranking import EventRanking
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey, Year
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class RankingsHelper:
    # (zach, 2021) - Stop updating these every year. They're used for converting between rankings -> rankings2.
    # We've been full rankings2 for a while now. We no longer need to keep updating these.
    SORT_ORDERS = {
        2020: [2, 3, 4, 5, 6],
        2019: [2, 3, 4, 5, 6],
        2018: [2, 3, 4, 5, 6],
        2017: [2, 3, 4, 5, 6, 7],
        2016: [2, 3, 4, 5, 6],
        2015: [2, 5, 3, 4, 7, 6],
        2014: [2, 3, 4, 5, 6],
        2013: [2, 3, 4, 5],
        2012: [2, 3, 4, 5],
        2011: [6, 7],
        2010: [3, 4, 5],
        2009: [6, 7, 8],
        2008: [6, 7, 8],
        2007: [6, 7, 8],
    }

    NO_RECORD_YEARS = {2010, 2015}

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

    """
    @classmethod
    def convert_rankings(cls, event_details):
        \"""
        Converts event_details.rankings to event_details.rankings2
        \"""
        if not event_details.rankings:
            return None

        year = event_details.game_year

        # Look up indexes
        mp_index = RankingIndexes.MATCHES_PLAYED.get(year)
        if mp_index is None:
            return
        ranking_index = RankingIndexes.RECORD_INDEXES.get(year)
        dq_index = None

        # Overwrite indexes in case thing are different
        for i, name in enumerate(event_details.rankings[0]):
            name = name.lower()
            if name == "played":
                mp_index = i
            if name == "dq":
                dq_index = i

        sort_order_indices = cls.SORT_ORDERS[year]
        # Special case for offseasons with different ordering
        if year == 2015 and event_details.rankings[0][3].lower() == "coopertition":
            sort_order_indices = [2, 3, 5, 4, 6, 7]

        rankings2 = []
        for row in event_details.rankings[1:]:
            if ranking_index is None:
                wins = 0
                losses = 0
                ties = 0
            elif type(ranking_index) == tuple:
                wins = row[ranking_index[0]]
                losses = row[ranking_index[1]]
                ties = row[ranking_index[2]]
            else:
                wins, losses, ties = row[ranking_index].split("-")

            if dq_index is None:
                dq = 0
            else:
                dq = int(row[dq_index])

            if year == 2015:
                qual_average = row[RankingIndexes.CUMULATIVE_RANKING_SCORE.get(year)]
            else:
                qual_average = None

            sort_orders = [row[index] for index in sort_order_indices]

            rankings2.append(
                cls.build_ranking(
                    year,
                    int(row[0]),
                    "frc{}".format(row[1]),
                    wins,
                    losses,
                    ties,
                    qual_average,
                    row[mp_index],
                    dq,
                    sort_orders,
                )
            )

        return rankings2
    """
