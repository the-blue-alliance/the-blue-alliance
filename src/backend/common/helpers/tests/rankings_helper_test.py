from datetime import datetime
from typing import cast, List

import pytest
from google.cloud import ndb

from backend.common.consts.event_type import EventType
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.helpers.rankings_helper import RankingsHelper
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails


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


@pytest.mark.parametrize("year", RankingsHelper.NO_RECORD_YEARS)
def test_build_ranking_no_record(year: int) -> None:
    ranking = RankingsHelper.build_ranking(
        year,
        1,  # rank
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        None,  # qual_average
        1,  # matches_played
        2,  # dq
        [],  # sort_orders
    )
    assert ranking["record"] is None


def test_build_ranking_record() -> None:
    ranking = RankingsHelper.build_ranking(
        2020,
        1,  # rank
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        None,  # qual_average
        1,  # matches_played
        2,  # dq
        [],  # sort_orders
    )
    assert ranking["record"] == {"losses": 2, "ties": 3, "wins": 1}


@pytest.mark.parametrize("year", RankingsHelper.QUAL_AVERAGE_YEARS)
def test_build_ranking_qual_average(year: int) -> None:
    qual_average = 39.18
    ranking = RankingsHelper.build_ranking(
        year,
        1,  # rank
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        qual_average,  # qual_average
        1,  # matches_played
        2,  # dq
        [],  # sort_orders
    )
    assert ranking["qual_average"] == qual_average


def test_build_ranking_no_qual_average() -> None:
    ranking = RankingsHelper.build_ranking(
        2020,
        1,  # rank
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        39.91,  # qual_average
        1,  # matches_played
        2,  # dq
        [],  # sort_orders
    )
    assert ranking["qual_average"] is None


def test_build_ranking_sort_orders_sanitized() -> None:
    ranking = RankingsHelper.build_ranking(
        2020,
        1,  # rank
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        39.91,  # qual_average
        1,  # matches_played
        2,  # dq
        cast(List[float], [0.0, 1.1, 2.2, "3.3", 4]),  # sort_orders - Casting for tests
    )
    assert ranking["sort_orders"] == [0.0, 1.1, 2.2, 3.3, 4.0]


def test_build_ranking_sort_orders_unsupported() -> None:
    ranking = RankingsHelper.build_ranking(
        2020,
        1,  # rank
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        39.91,  # qual_average
        1,  # matches_played
        2,  # dq
        cast(List[float], [1.1, None]),  # sort_orders - Casting for tests
    )
    assert ranking["sort_orders"] == [1.1, 0.0]


@pytest.mark.parametrize("rank", [1, "1", 1.0])
def test_build_ranking_sort_orders_rank(rank) -> None:
    ranking = RankingsHelper.build_ranking(
        2020,
        rank,
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        39.91,  # qual_average
        1,  # matches_played
        2,  # dq
        [],  # sort_orders
    )
    assert ranking["rank"] == 1


@pytest.mark.parametrize("matches_played", [12, "12", 12.0])
def test_build_ranking_sort_orders_matches_played(matches_played) -> None:
    ranking = RankingsHelper.build_ranking(
        2020,
        1,
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        39.91,  # qual_average
        matches_played,  # matches_played
        2,  # dq
        [],  # sort_orders
    )
    assert ranking["matches_played"] == 12


@pytest.mark.parametrize("dq", [2, "2", 2.0])
def test_build_ranking_sort_orders_dq(dq) -> None:
    ranking = RankingsHelper.build_ranking(
        2020,
        1,
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        39.91,  # qual_average
        1,  # matches_played
        dq,  # dq
        [],  # sort_orders
    )
    assert ranking["dq"] == 2.0


def test_build_ranking() -> None:
    ranking = RankingsHelper.build_ranking(
        2020,
        1,  # rank
        "frc7332",  # team_key
        1,  # wins
        2,  # losses
        3,  # ties
        None,  # qual_average
        1,  # matches_played
        2,  # dq
        [1.1, 2.2],  # sort_orders
    )
    assert ranking["rank"] == 1
    assert ranking["team_key"] == "frc7332"
    assert ranking["record"] == {"losses": 2, "ties": 3, "wins": 1}
    assert ranking["qual_average"] is None
    assert ranking["matches_played"] == 1
    assert ranking["dq"] == 2
    assert ranking["sort_orders"] == [1.1, 2.2]


@pytest.mark.parametrize("year", SORT_ORDER_INFO.keys())
def test_get_sort_order_info(year, ndb_context) -> None:
    event_details = EventDetails(key=ndb.Key(EventDetails, "{}zor".format(year)))
    sort_order_info = RankingsHelper.get_sort_order_info(event_details)
    assert sort_order_info == SORT_ORDER_INFO[year]


@pytest.mark.parametrize(
    "event_key, event_type, expected_year",
    [
        ("2015mttd", None, 2014),
        ("2015miket", None, 2015),
        ("2021irhag", None, 2021),
        ("2021isoir1", EventType.OFFSEASON, 2020),
    ],
)
def test_get_sort_order_info_year(
    event_key, event_type, expected_year, ndb_context
) -> None:
    if event_type:
        _create_test_event(event_key, event_type)
    else:
        _create_test_event(event_key)

    event_details = EventDetails(key=ndb.Key(EventDetails, event_key))
    sort_order_info = RankingsHelper.get_sort_order_info(event_details)
    assert sort_order_info == SORT_ORDER_INFO[expected_year]
