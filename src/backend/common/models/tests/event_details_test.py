from backend.common.consts.ranking_sort_orders import (
    SORT_ORDER_INFO as RANKING_SORT_ORDERS,
)
from backend.common.models.event_details import EventDetails, RenderedRankings
from backend.common.models.event_ranking import EventRanking
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


def test_render_rankings_no_data() -> None:
    details = EventDetails(id="2019nyny")
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=None,
        sort_order_info=RANKING_SORT_ORDERS[2019],
        extra_stats_info=[],
    )


def test_render_rankings_no_data_very_old() -> None:
    details = EventDetails(id="2000nyny")
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=None,
        sort_order_info=None,
        extra_stats_info=[],
    )


def test_render_rankings_with_extra_stats() -> None:
    details = EventDetails(
        id="2019nyny",
        rankings2=[
            EventRanking(
                rank=1,
                team_key="frc254",
                record=WLTRecord(
                    wins=1,
                    losses=0,
                    ties=0,
                ),
                qual_average=None,
                matches_played=1,
                dq=0,
                sort_orders=[0, 0, 0, 0, 0],
            )
        ],
    )
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=details.rankings2,
        sort_order_info=RANKING_SORT_ORDERS[2019],
        extra_stats_info=[
            RankingSortOrderInfo(
                name="Total Ranking Points",
                precision=0,
            )
        ],
    )


def test_render_rankings_with_extra_stats_per_match() -> None:
    details = EventDetails(
        id="2016nyny",
        rankings2=[
            EventRanking(
                rank=1,
                team_key="frc254",
                record=WLTRecord(
                    wins=1,
                    losses=0,
                    ties=0,
                ),
                qual_average=None,
                matches_played=1,
                dq=0,
                sort_orders=[0, 0, 0, 0, 0],
            )
        ],
    )
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=details.rankings2,
        sort_order_info=RANKING_SORT_ORDERS[2016],
        extra_stats_info=[
            RankingSortOrderInfo(
                name="Ranking Score/Match",
                precision=2,
            )
        ],
    )


def test_render_rankings_with_extra_stats_per_match_unplayed() -> None:
    details = EventDetails(
        id="2016nyny",
        rankings2=[
            EventRanking(
                rank=1,
                team_key="frc254",
                record=WLTRecord(
                    wins=0,
                    losses=0,
                    ties=0,
                ),
                qual_average=None,
                matches_played=0,
                dq=0,
                sort_orders=[0, 0, 0, 0, 0],
            )
        ],
    )
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=details.rankings2,
        sort_order_info=RANKING_SORT_ORDERS[2016],
        extra_stats_info=[
            RankingSortOrderInfo(
                name="Ranking Score/Match",
                precision=2,
            )
        ],
    )


def test_render_rankings_with_extra_stats_per_match_2015() -> None:
    details = EventDetails(
        id="2015nyny",
        rankings2=[
            EventRanking(
                rank=1,
                team_key="frc254",
                record=WLTRecord(
                    wins=1,
                    losses=0,
                    ties=0,
                ),
                qual_average=10,
                matches_played=1,
                dq=0,
                sort_orders=[0, 0, 0, 0, 0],
            )
        ],
    )
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=details.rankings2,
        sort_order_info=RANKING_SORT_ORDERS[2015],
        extra_stats_info=[],
    )


def test_render_rankings_with_extra_stats_per_match_2015mttd() -> None:
    # 2015mttd played the 2014 game
    details = EventDetails(
        id="2015mttd",
    )
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=details.rankings2,
        sort_order_info=RANKING_SORT_ORDERS[2014],
        extra_stats_info=[],
    )
