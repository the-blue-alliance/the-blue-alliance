from datetime import datetime

import pytest

from backend.common.consts.event_type import EventType
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails, RenderedRankings
from backend.common.models.event_ranking import EventRanking
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


def _create_test_event(event_key: str, event_type: EventType = EventType.REGIONAL):
    year = int(event_key[:4])
    short = event_key[4:]
    e = Event(
        id=event_key,
        year=year,
        event_type_enum=event_type,
        official=True,
        start_date=datetime(year, 3, 1),
        event_short=short,
    )
    e.put()


def test_render_rankings_no_data() -> None:
    details = EventDetails(id="2019nyny")
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=[],
        sort_order_info=SORT_ORDER_INFO[2019],
        extra_stats_info=[],
    )


def test_render_rankings_no_data_very_old() -> None:
    details = EventDetails(id="2000nyny")
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=[],
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
        sort_order_info=SORT_ORDER_INFO[2019],
        extra_stats_info=[
            RankingSortOrderInfo(
                name="Total Ranking Points",
                precision=0,
            )
        ],
    )


def test_render_rankings_with_no_sort_orders() -> None:
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
                sort_orders=[],
            )
        ],
    )
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=details.rankings2,
        sort_order_info=SORT_ORDER_INFO[2019],
        extra_stats_info=[],
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
        sort_order_info=SORT_ORDER_INFO[2016],
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
        sort_order_info=SORT_ORDER_INFO[2016],
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
        sort_order_info=SORT_ORDER_INFO[2015],
        extra_stats_info=[],
    )


@pytest.mark.parametrize(
    "event_key, event_type, expected_year",
    [
        ("2015mttd", None, 2014),
        ("2015miket", None, 2015),
        ("2021irhag", None, 2021),
        ("2021isoir1", EventType.OFFSEASON, 2020),
    ],
)
def test_game_year(event_key, event_type, expected_year, ndb_context) -> None:
    if event_type:
        _create_test_event(event_key, event_type)
    else:
        _create_test_event(event_key)

    details = EventDetails(id=event_key)
    assert details.game_year == expected_year


@pytest.mark.parametrize(
    "event_key, event_type, expected_year",
    [
        ("2015mttd", None, 2014),
        ("2015miket", None, 2015),
        ("2021irhag", None, 2021),
        ("2021isoir1", EventType.OFFSEASON, 2020),
    ],
)
def test_render_rankings_game_year(
    event_key, event_type, expected_year, ndb_context
) -> None:
    if event_type:
        _create_test_event(event_key, event_type)
    else:
        _create_test_event(event_key)

    details = EventDetails(id=event_key)
    rankings = details.renderable_rankings
    assert rankings == RenderedRankings(
        rankings=[],
        sort_order_info=SORT_ORDER_INFO[expected_year],
        extra_stats_info=[],
    )


def test_rankings_table_game_year_2021(ndb_context) -> None:
    event_key = "2021miket"
    _create_test_event(event_key)

    details = EventDetails(
        id=event_key,
        rankings2=[
            EventRanking(
                rank=1,
                team_key="frc254",
                record=None,
                qual_average=None,
                matches_played=0,
                dq=0,
                sort_orders=[1, 2, 3, 4, 5, 6],
            )
        ],
    )
    assert details.rankings_table == [
        [
            "Rank",
            "Team",
            "Overall Score",
            "Galactic Search",
            "Auto-Nav",
            "Hyperdrive",
            "Interstellar Accuracy",
            "Power Port",
        ],
        [1, "254", "1.00", "2.00", "3.00", "4.00", "5.00", "6.00"],
    ]


def test_rankings_table_game_no_sort_orders(ndb_context) -> None:
    event_key = "2024test"
    _create_test_event(event_key)

    details = EventDetails(
        id=event_key,
        rankings2=[
            EventRanking(
                rank=1,
                team_key="frc254",
                record=None,
                qual_average=None,
                matches_played=0,
                dq=0,
                sort_orders=[],
            )
        ],
    )
    assert details.rankings_table == [
        [
            "Rank",
            "Team",
            "Ranking Score",
            "Avg Coop",
            "Avg Match",
            "Avg Auto",
            "Avg Stage",
            "DQ",
            "Played",
        ],
        [1, "254", 0, 0],
    ]


def test_rankings_table_game_year_2021_offseason(ndb_context) -> None:
    event_key = "2021isoir1"
    _create_test_event(event_key, EventType.OFFSEASON)

    details = EventDetails(
        id=event_key,
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
                sort_orders=[1, 2, 3, 4],
            )
        ],
    )
    assert details.rankings_table == [
        [
            "Rank",
            "Team",
            "Ranking Score",
            "Auto",
            "End Game",
            "Teleop Cell + CPanel",
            "Record (W-L-T)",
            "DQ",
            "Played",
            "Total Ranking Points*",
        ],
        [1, "254", "1.00", "2", "3", "4", "1-0-0", 0, 1, "1"],
    ]
