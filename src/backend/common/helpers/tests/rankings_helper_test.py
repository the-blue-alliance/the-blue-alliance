from typing import cast, List

import pytest
from google.cloud import ndb

from backend.common.helpers.rankings_helper import RankingsHelper
from backend.common.models.event_details import EventDetails


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


@pytest.mark.parametrize("year", RankingsHelper.SORT_ORDER_INFO.keys())
def test_get_sort_order_info(year, ndb_client: ndb.Client) -> None:
    with ndb_client.context():
        event_details = EventDetails(key=ndb.Key(EventDetails, "{}zor".format(year)))
    assert (
        RankingsHelper.get_sort_order_info(event_details)
        == RankingsHelper.SORT_ORDER_INFO[year]
    )


def test_get_sort_order_info_2015mttd(ndb_client: ndb.Client) -> None:
    with ndb_client.context():
        event_details = EventDetails(key=ndb.Key(EventDetails, "2015mttd"))
    assert (
        RankingsHelper.get_sort_order_info(event_details)
        == RankingsHelper.SORT_ORDER_INFO[2014]
    )
