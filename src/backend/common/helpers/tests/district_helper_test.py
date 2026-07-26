import json
from typing import cast
from unittest import mock

import pytest
from pyre_extensions import none_throws

from backend.common.helpers.district_helper import (
    DistrictHelper,
    DistrictRankingTeamTotal,
    DistrictRankingTiebreakers,
    TeamAtEventDistrictPoints,
)
from backend.common.models.district_advancement import ApiDistrictRankingTeamData
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.keys import Year
from backend.common.models.team import Team


@pytest.mark.parametrize(
    "event_key",
    [
        "2024nytr",  # A 2024 event with a backup team
        "2024necmp",  # A 2024 event where one alliance wins no matches
        "2024test",  # A 2024 event with backup robot wins in the final
        "2023onlon",  # A 2023 event with backup robot wins in the final
        "2023mijac",  # A 2023 event
        "2023njfla",  # A 2023 event with backup team district points (wins and losses)
        "2023micmp",  # A double elimination DCMP with four divisions
        "2022on305",  # A 2022 single day event
        "2019nyny",  # A regular event
        "2015nyny",  # 2015 is special (average score ranking)
        "2018necmp",  # DCMP has 3x multiplier
        "2019micmp",  # A DCMP with divisions
        "2019micmp3",  # A DCMP Division
        "2015micmp",  # Special case because octofinals
        "2012pah",  # Pre-2014 accounted awards differently, used WLT for quals
    ],
)
def test_calc_event_points(
    event_key, ndb_stub, setup_full_event, test_data_importer
) -> None:
    setup_full_event(event_key)

    event = Event.get_by_id(event_key)
    assert event is not None
    event_points = DistrictHelper.calculate_event_points(event)

    with open(
        test_data_importer._get_path(
            __file__, f"data/{event_key}_district_points.json"
        ),
        "r",
    ) as f:
        expected_event_points = json.load(f)

    assert event_points == expected_event_points


def test_calc_event_points_excludes_dq_from_match_score_tiebreaker(
    setup_full_event,
) -> None:
    # 2023onlon_qm27 scored 128 with frc6162 on the alliance but frc6162 was
    # DQ'd in that match; the score must not count toward frc6162's top-3
    # match score tiebreaker.
    setup_full_event("2023onlon")
    event = none_throws(Event.get_by_id("2023onlon"))
    event_points = DistrictHelper.calculate_event_points(event)
    assert 128 not in event_points["tiebreakers"]["frc6162"]["highest_match_scores"]


def test_calculate_multi_event_rankings_all_teams_filtered(setup_full_event) -> None:
    setup_full_event("2019nyny")
    setup_full_event("2019micmp3")
    setup_full_event("2019micmp")

    events = [
        none_throws(Event.get_by_id("2019nyny")),
        none_throws(Event.get_by_id("2019micmp3")),
        none_throws(Event.get_by_id("2019micmp")),
    ]

    rankings = DistrictHelper.calculate_rankings(events, [], 2019, None)
    assert rankings == {}


def test_calculate_multi_event_rankings(setup_full_event) -> None:
    setup_full_event("2019nyny")
    setup_full_event("2019micmp3")
    setup_full_event("2019micmp")

    events = [
        none_throws(Event.get_by_id("2019nyny")),
        none_throws(Event.get_by_id("2019micmp3")),
        none_throws(Event.get_by_id("2019micmp")),
    ]
    teams = [
        none_throws(Team.get_by_id("frc694")),
        none_throws(Team.get_by_id("frc4362")),
    ]

    rankings = DistrictHelper.calculate_rankings(events, teams, 2019, None)
    assert len(rankings) == 2  # should match the two teams we passed
    assert rankings["frc694"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[0],
                TeamAtEventDistrictPoints(
                    alliance_points=16,
                    award_points=5,
                    elim_points=30,
                    qual_points=19,
                    total=70,
                ),
            )
        ],
        point_total=70,
        match_scores=[94, 91, 89],
        rookie_bonus=0,
        other_bonus=0,
        single_event_bonus=0,
        adjustments=0,
        tiebreakers=DistrictRankingTiebreakers(*[30, 30, 16, 16, 19]),
    )
    assert rankings["frc4362"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[1],
                TeamAtEventDistrictPoints(
                    alliance_points=42,
                    award_points=15,
                    elim_points=90,
                    qual_points=60,
                    total=207,
                ),
            ),
            (
                events[2],
                TeamAtEventDistrictPoints(
                    alliance_points=0,
                    award_points=0,
                    elim_points=60,
                    qual_points=0,
                    total=60,
                ),
            ),
        ],
        point_total=267,
        match_scores=[127, 121, 113],
        rookie_bonus=0,
        single_event_bonus=0,
        other_bonus=0,
        adjustments=0,
        tiebreakers=DistrictRankingTiebreakers(*[150, 90, 42, 42, 60]),
    )


def test_2022_back_to_back_single_day_bonus(setup_full_event) -> None:
    setup_full_event("2022on305")
    setup_full_event("2022on306")

    events = [
        none_throws(Event.get_by_id("2022on305")),
        none_throws(Event.get_by_id("2022on306")),
    ]
    teams = [
        none_throws(Team.get_by_id("frc2200")),
        none_throws(Team.get_by_id("frc610")),
        none_throws(Team.get_by_id("frc1241")),
    ]

    rankings = DistrictHelper.calculate_rankings(events, teams, 2022, None)
    assert len(rankings) == 3
    assert rankings["frc2200"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[0],
                TeamAtEventDistrictPoints(
                    alliance_points=16,
                    award_points=0,
                    elim_points=20,
                    qual_points=22,
                    total=58,
                ),
            ),
            (
                events[1],
                TeamAtEventDistrictPoints(
                    alliance_points=16,
                    award_points=5,
                    elim_points=20,
                    qual_points=22,
                    total=63,
                ),
            ),
        ],
        point_total=123,
        match_scores=[93, 82, 82],
        rookie_bonus=0,
        single_event_bonus=0,
        other_bonus=2,
        adjustments=0,
        tiebreakers=DistrictRankingTiebreakers(*[40, 20, 32, 16, 44]),
    )
    assert rankings["frc610"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[0],
                TeamAtEventDistrictPoints(
                    alliance_points=16,
                    award_points=5,
                    elim_points=20,
                    qual_points=18,
                    total=59,
                ),
            )
        ],
        point_total=59,
        match_scores=[73, 59, 57],
        rookie_bonus=0,
        single_event_bonus=0,
        other_bonus=0,
        adjustments=0,
        tiebreakers=DistrictRankingTiebreakers(*[20, 20, 16, 16, 18]),
    )
    assert rankings["frc1241"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[1],
                TeamAtEventDistrictPoints(
                    alliance_points=14,
                    award_points=5,
                    elim_points=10,
                    qual_points=12,
                    total=41,
                ),
            )
        ],
        point_total=41,
        match_scores=[67, 56, 45],
        rookie_bonus=0,
        single_event_bonus=0,
        other_bonus=0,
        adjustments=0,
        tiebreakers=DistrictRankingTiebreakers(*[10, 10, 14, 14, 12]),
    )


@pytest.mark.parametrize(
    "year,rookie_year,bonus",
    [
        (2020, 2020, 10),
        (2020, 2019, 5),
        (2022, 2022, 10),
        (2022, 2021, 10),
        (2022, 2020, 5),
        (2022, 2019, 0),
        (2023, 2023, 10),
        (2023, 2022, 5),
        (2023, 2021, 5),
        (2023, 2020, 0),
        (2023, 2019, 0),
    ],
)
def test_pandemic_rookie_edge_cases(year: Year, rookie_year: Year, bonus: int) -> None:
    assert DistrictHelper._get_rookie_bonus(year, rookie_year) == bonus


def test_calc_rankings_tolerates_legacy_tiebreaker_key(setup_full_event) -> None:
    # Pre-migration EventDetails.district_points entries store
    # "highest_qual_scores" instead of the renamed "highest_match_scores".
    # Rankings calc reads stored JSON directly and must not KeyError on those.
    setup_full_event("2019nyny")

    event_details = none_throws(EventDetails.get_by_id("2019nyny"))
    district_points = none_throws(event_details.district_points)
    for tiebreakers in district_points["tiebreakers"].values():
        # Cast away the TypedDict to simulate legacy on-disk JSON shape.
        legacy: dict[str, object] = cast(dict[str, object], tiebreakers)
        legacy["highest_qual_scores"] = legacy.pop("highest_match_scores", [])
    event_details.district_points = district_points
    event_details.put()

    event = none_throws(Event.get_by_id("2019nyny"))
    event.prep_details()

    teams = [none_throws(Team.get_by_id("frc694"))]
    rankings = DistrictHelper.calculate_rankings([event], teams, 2019, None)

    # Tiebreak scores aren't recovered from the old key, but the calc completes.
    assert rankings["frc694"]["match_scores"] == []


def test_hq_adjustments(setup_full_event) -> None:
    setup_full_event("2019nyny")

    events = [
        none_throws(Event.get_by_id("2019nyny")),
    ]
    teams = [
        none_throws(Team.get_by_id("frc694")),
    ]

    rankings = DistrictHelper.calculate_rankings(
        events, teams, 2022, adjustments={"frc694": 5}
    )
    assert len(rankings) == 1

    assert rankings["frc694"] == DistrictRankingTeamTotal(
        event_points=[
            (
                events[0],
                TeamAtEventDistrictPoints(
                    alliance_points=16,
                    award_points=5,
                    elim_points=30,
                    qual_points=19,
                    total=70,
                ),
            )
        ],
        point_total=75,
        match_scores=[94, 91, 89],
        rookie_bonus=0,
        other_bonus=0,
        single_event_bonus=0,
        adjustments=5,
        tiebreakers=DistrictRankingTiebreakers(*[30, 30, 16, 16, 19]),
    )


# --- _break_ties_with_first_rank ---


def _mock_event(first_api_code: str) -> Event:
    event = mock.MagicMock(spec=Event)
    event.first_api_code = first_api_code
    return event


def _team_total(
    *,
    point_total: int,
    rookie_bonus: int,
    event_points: list[tuple[Event, TeamAtEventDistrictPoints]],
    tiebreakers: DistrictRankingTiebreakers = DistrictRankingTiebreakers(0, 0, 0, 0, 0),
    match_scores: list[int] | None = None,
) -> DistrictRankingTeamTotal:
    return DistrictRankingTeamTotal(
        event_points=event_points,
        point_total=point_total,
        tiebreakers=tiebreakers,
        match_scores=match_scores or [],
        rookie_bonus=rookie_bonus,
        single_event_bonus=0,
        other_bonus=0,
        adjustments=0,
    )


def _api_data(
    *,
    rank: int,
    total_points: int = 50,
    team_age_points: int = 0,
    event1_code: str | None = "ABC",
    event1_points: int | None = 25,
    event2_code: str | None = "DEF",
    event2_points: int | None = 25,
    district_cmp_code: str | None = None,
    district_cmp_points: int | None = None,
) -> ApiDistrictRankingTeamData:
    return ApiDistrictRankingTeamData(
        rank=rank,
        total_points=total_points,
        team_age_points=team_age_points,
        event1_code=event1_code,
        event1_points=event1_points,
        event2_code=event2_code,
        event2_points=event2_points,
        district_cmp_code=district_cmp_code,
        district_cmp_points=district_cmp_points,
    )


def _tied_team_totals() -> dict[str, DistrictRankingTeamTotal]:
    # Two teams identical on every TBA tiebreaker but different events.
    event_a1 = _mock_event("ABC")
    event_a2 = _mock_event("DEF")
    event_b1 = _mock_event("ABC")
    event_b2 = _mock_event("DEF")
    return {
        "frcA": _team_total(
            point_total=50,
            rookie_bonus=0,
            event_points=[
                (
                    event_a1,
                    TeamAtEventDistrictPoints(
                        qual_points=10,
                        elim_points=5,
                        alliance_points=5,
                        award_points=5,
                        total=25,
                    ),
                ),
                (
                    event_a2,
                    TeamAtEventDistrictPoints(
                        qual_points=10,
                        elim_points=5,
                        alliance_points=5,
                        award_points=5,
                        total=25,
                    ),
                ),
            ],
        ),
        "frcB": _team_total(
            point_total=50,
            rookie_bonus=0,
            event_points=[
                (
                    event_b1,
                    TeamAtEventDistrictPoints(
                        qual_points=10,
                        elim_points=5,
                        alliance_points=5,
                        award_points=5,
                        total=25,
                    ),
                ),
                (
                    event_b2,
                    TeamAtEventDistrictPoints(
                        qual_points=10,
                        elim_points=5,
                        alliance_points=5,
                        award_points=5,
                        total=25,
                    ),
                ),
            ],
        ),
    }


def test_break_ties_full_agreement_uses_first_rank() -> None:
    team_totals = _tied_team_totals()
    api_team_data = {
        "frcA": _api_data(rank=2),
        "frcB": _api_data(rank=1),
    }
    result = DistrictHelper._break_ties_with_first_rank(team_totals, api_team_data)
    assert list(result.keys()) == ["frcB", "frcA"]


def test_break_ties_total_points_disagree_leaves_order() -> None:
    team_totals = _tied_team_totals()
    api_team_data = {
        "frcA": _api_data(rank=2),
        "frcB": _api_data(rank=1, total_points=51),  # mismatch
    }
    result = DistrictHelper._break_ties_with_first_rank(team_totals, api_team_data)
    assert list(result.keys()) == ["frcA", "frcB"]


def test_break_ties_per_event_points_disagree_leaves_order() -> None:
    team_totals = _tied_team_totals()
    api_team_data = {
        "frcA": _api_data(rank=2),
        "frcB": _api_data(rank=1, event1_points=24),  # 24 != TBA's 25
    }
    result = DistrictHelper._break_ties_with_first_rank(team_totals, api_team_data)
    assert list(result.keys()) == ["frcA", "frcB"]


def test_break_ties_event_code_mismatch_leaves_order() -> None:
    team_totals = _tied_team_totals()
    api_team_data = {
        "frcA": _api_data(rank=2),
        # frcB's TBA event "DEF" isn't in FIRST's reported events for this team
        "frcB": _api_data(rank=1, event2_code="ZZZ"),
    }
    result = DistrictHelper._break_ties_with_first_rank(team_totals, api_team_data)
    assert list(result.keys()) == ["frcA", "frcB"]


def test_break_ties_team_age_points_disagree_leaves_order() -> None:
    team_totals = _tied_team_totals()
    api_team_data = {
        "frcA": _api_data(rank=2),
        "frcB": _api_data(rank=1, team_age_points=5),  # TBA rookie_bonus is 0
    }
    result = DistrictHelper._break_ties_with_first_rank(team_totals, api_team_data)
    assert list(result.keys()) == ["frcA", "frcB"]


def test_break_ties_missing_api_data_leaves_order() -> None:
    team_totals = _tied_team_totals()
    api_team_data = {"frcA": _api_data(rank=2)}  # frcB missing
    result = DistrictHelper._break_ties_with_first_rank(team_totals, api_team_data)
    assert list(result.keys()) == ["frcA", "frcB"]


def test_break_ties_untied_teams_unaffected() -> None:
    # frcA and frcB are NOT tied (different point_totals); FIRST's ranks
    # disagree with TBA's order, but we shouldn't touch them.
    event_a = _mock_event("ABC")
    event_b = _mock_event("ABC")
    team_totals = {
        "frcA": _team_total(
            point_total=60,
            rookie_bonus=0,
            event_points=[
                (
                    event_a,
                    TeamAtEventDistrictPoints(
                        qual_points=10,
                        elim_points=10,
                        alliance_points=10,
                        award_points=30,
                        total=60,
                    ),
                )
            ],
        ),
        "frcB": _team_total(
            point_total=50,
            rookie_bonus=0,
            event_points=[
                (
                    event_b,
                    TeamAtEventDistrictPoints(
                        qual_points=10,
                        elim_points=10,
                        alliance_points=5,
                        award_points=25,
                        total=50,
                    ),
                )
            ],
        ),
    }
    api_team_data = {
        "frcA": _api_data(
            rank=2,
            total_points=60,
            event1_points=60,
            event2_code=None,
            event2_points=None,
        ),
        "frcB": _api_data(
            rank=1,
            total_points=50,
            event1_points=50,
            event2_code=None,
            event2_points=None,
        ),
    }
    result = DistrictHelper._break_ties_with_first_rank(team_totals, api_team_data)
    assert list(result.keys()) == ["frcA", "frcB"]
