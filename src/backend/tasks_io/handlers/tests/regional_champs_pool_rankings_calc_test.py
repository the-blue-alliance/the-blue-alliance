from unittest import mock

from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.helpers.district_helper import (
    DistrictRankingTeamTotal,
)
from backend.common.helpers.regional_champs_pool_helper import RegionalChampsPoolHelper
from backend.common.models.event import Event
from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.common.models.regional_champs_pool import RegionalChampsPool
from backend.common.models.regional_pool_ranking import RegionalPoolRanking


def test_enqueue_bad_year(tasks_client: Client) -> None:
    resp = tasks_client.get(
        "/tasks/math/enqueue/regional_champs_pool_rankings_calc/2020"
    )
    assert resp.status_code == 404


@mock.patch.object(RegionalChampsPoolHelper, "calculate_rankings")
def test_calc(calc_mock: mock.Mock, tasks_client: Client) -> None:
    event = Event(
        id="2025event",
        year=2025,
        event_short="event",
        event_type_enum=EventType.REGIONAL,
    )
    event.put()

    calc_mock.return_value = {
        "frc254": DistrictRankingTeamTotal(
            event_points=[
                (
                    event,
                    TeamAtEventDistrictPoints(
                        event_key=event.key_name,
                        qual_points=10,
                        elim_points=0,
                        alliance_points=0,
                        award_points=0,
                        total=10,
                    ),
                ),
            ],
            point_total=10,
            tiebreakers=[],
            qual_scores=[],
            rookie_bonus=0,
            other_bonus=0,
        )
    }

    resp = tasks_client.get("/tasks/math/do/regional_champs_pool_rankings_calc/2025")
    assert resp.status_code == 200
    assert b"Finished calculating regional pool rankings for: 2025" in resp.data

    regional_pool = RegionalChampsPool.get_by_id(
        RegionalChampsPool.render_key_name(2025)
    )
    assert regional_pool is not None
    assert regional_pool.rankings == [
        RegionalPoolRanking(
            rank=1,
            team_key="frc254",
            event_points=[
                TeamAtEventDistrictPoints(
                    event_key="2025event",
                    qual_points=10,
                    elim_points=0,
                    alliance_points=0,
                    award_points=0,
                    total=10,
                ),
            ],
            rookie_bonus=0,
            point_total=10,
        ),
    ]


@mock.patch.object(RegionalChampsPoolHelper, "calculate_rankings")
def test_calc_doesnt_write_out_in_taskqueue(
    calc_mock: mock.Mock, tasks_client: Client
) -> None:
    event = Event(
        id="2025event",
        year=2025,
        event_short="event",
        event_type_enum=EventType.REGIONAL,
    )
    event.put()

    calc_mock.return_value = {
        "frc254": DistrictRankingTeamTotal(
            event_points=[
                (
                    event,
                    TeamAtEventDistrictPoints(
                        event_key=event.key_name,
                        qual_points=10,
                        elim_points=0,
                        alliance_points=0,
                        award_points=0,
                        total=10,
                    ),
                ),
            ],
            point_total=10,
            tiebreakers=[],
            qual_scores=[],
            rookie_bonus=0,
            other_bonus=0,
        )
    }

    headers = {
        "X-Appengine-Taskname": "test",
    }
    resp = tasks_client.get(
        "/tasks/math/do/regional_champs_pool_rankings_calc/2025", headers=headers
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    regional_pool = RegionalChampsPool.get_by_id(
        RegionalChampsPool.render_key_name(2025)
    )
    assert regional_pool is not None
    assert regional_pool.rankings == [
        RegionalPoolRanking(
            rank=1,
            team_key="frc254",
            event_points=[
                TeamAtEventDistrictPoints(
                    event_key="2025event",
                    qual_points=10,
                    elim_points=0,
                    alliance_points=0,
                    award_points=0,
                    total=10,
                ),
            ],
            rookie_bonus=0,
            point_total=10,
        ),
    ]
