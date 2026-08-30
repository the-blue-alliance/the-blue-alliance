from typing import Optional
from unittest import mock

import pytest
from freezegun import freeze_time
from google.appengine.ext import testbed
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.cmp_qualification import CmpQualificationMethod
from backend.common.consts.event_type import EventType
from backend.common.futures import InstantFuture
from backend.common.helpers.district_helper import (
    DistrictHelper,
    DistrictRankingTeamTotal,
)
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.district import District
from backend.common.models.district_advancement import DistrictAdvancementCutoffs
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.event import Event
from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


def test_enqueue_bad_year(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/district_rankings_calc/asdf")
    assert resp.status_code == 404


@freeze_time("2020-4-1")
def test_enqueue_no_events(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/district_rankings_calc/2020")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued for: []"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@freeze_time("2020-4-1")
def test_enqueue_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get(
        "/tasks/math/enqueue/district_rankings_calc/2020",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert resp.data == b""

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_enqueue_event(
    district_rankings_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    district_rankings_mock.return_value = InstantFuture({})
    District(
        id="2020test",
        year=2020,
        abbreviation="test",
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/district_rankings_calc/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    taskqueue_stub.Clear()


@mock.patch.object(SeasonHelper, "get_current_season")
@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_enqueue_default_year(
    district_rankings_mock,
    season_helper_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    season_helper_mock.return_value = 2020
    district_rankings_mock.return_value = InstantFuture({})
    District(
        id="2020test",
        year=2020,
        abbreviation="test",
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/district_rankings_calc")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    taskqueue_stub.Clear()


def test_calc_no_district(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/do/district_rankings_calc/2020ne")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "event_type,is_dcmp",
    [
        (EventType.REGIONAL, False),
        (EventType.DISTRICT_CMP, True),
        (EventType.DISTRICT_CMP_DIVISION, True),
    ],
)
@mock.patch.object(DistrictHelper, "calculate_rankings")
def test_calc(
    calc_mock: mock.Mock, event_type: EventType, is_dcmp: bool, tasks_client: Client
) -> None:
    District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
    ).put()
    event = Event(
        id="2020event", year=2020, event_short="event", event_type_enum=event_type
    )
    calc_mock.return_value = {
        "frc254": DistrictRankingTeamTotal(
            event_points=[
                (
                    event,
                    TeamAtEventDistrictPoints(
                        event_key=event.key_name,
                        district_cmp=False,
                        qual_points=0,
                        elim_points=0,
                        alliance_points=0,
                        award_points=0,
                        total=0,
                    ),
                )
            ],
            point_total=0,
            tiebreakers=[],
            match_scores=[],
            rookie_bonus=0,
            single_event_bonus=0,
            other_bonus=0,
            adjustments=5,
        )
    }

    resp = tasks_client.get("/tasks/math/do/district_rankings_calc/2020ne")
    assert resp.status_code == 200
    assert b"Finished calculating rankings for: 2020ne" in resp.data

    district = District.get_by_id("2020ne")
    assert district is not None
    assert district.rankings == [
        DistrictRanking(
            rank=1,
            team_key="frc254",
            event_points=[
                TeamAtEventDistrictPoints(
                    event_key="2020event",
                    district_cmp=is_dcmp,
                    qual_points=0,
                    elim_points=0,
                    alliance_points=0,
                    award_points=0,
                    total=0,
                ),
            ],
            rookie_bonus=0,
            adjustments=5,
            point_total=0,
        )
    ]


@mock.patch.object(DistrictHelper, "calculate_rankings")
def test_calc_no_output_in_taskqueue(
    calc_mock: mock.Mock, tasks_client: Client
) -> None:
    District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
    ).put()
    calc_mock.return_value = {
        "frc254": DistrictRankingTeamTotal(
            event_points=[],
            point_total=0,
            tiebreakers=[],
            match_scores=[],
            rookie_bonus=0,
            single_event_bonus=0,
            other_bonus=0,
            adjustments=0,
        )
    }

    resp = tasks_client.get(
        "/tasks/math/do/district_rankings_calc/2020ne",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert resp.data == b""


def _team_total(
    qual_event: Event,
    qual_points: int,
    dcmp_event: Optional[Event] = None,
    dcmp_points: int = 0,
    dcmp_award_points: int = 0,
) -> DistrictRankingTeamTotal:
    event_points = [
        (
            qual_event,
            TeamAtEventDistrictPoints(
                event_key=qual_event.key_name,
                district_cmp=False,
                qual_points=qual_points,
                elim_points=0,
                alliance_points=0,
                award_points=0,
                total=qual_points,
            ),
        )
    ]
    if dcmp_event is not None:
        event_points.append(
            (
                dcmp_event,
                TeamAtEventDistrictPoints(
                    event_key=dcmp_event.key_name,
                    district_cmp=True,
                    qual_points=dcmp_points,
                    elim_points=0,
                    alliance_points=0,
                    award_points=dcmp_award_points,
                    total=dcmp_points + dcmp_award_points,
                ),
            )
        )
    return DistrictRankingTeamTotal(
        event_points=event_points,
        point_total=qual_points + dcmp_points + dcmp_award_points,
        tiebreakers=[],
        match_scores=[],
        rookie_bonus=0,
        single_event_bonus=0,
        other_bonus=0,
        adjustments=0,
    )


@mock.patch.object(DistrictHelper, "calculate_rankings")
def test_calc_writes_advancement_cutoffs(
    calc_mock: mock.Mock, tasks_client: Client
) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()
    qual_event = Event(
        id="2020ndis", year=2020, event_short="ndis", event_type_enum=EventType.DISTRICT
    )
    dcmp_event = Event(
        id="2020necmp",
        year=2020,
        event_short="necmp",
        event_type_enum=EventType.DISTRICT_CMP,
    )

    # 64 DCMP slots; frc10 declines, so frc65 takes the passed-down slot.
    attending = (set(range(1, 65)) - {10}) | {65}
    calc_mock.return_value = {
        f"frc{i}": _team_total(
            qual_event,
            100 - i,
            dcmp_event if i in attending else None,
            5 if i in attending else 0,
        )
        for i in range(1, 71)
    }

    resp = tasks_client.get("/tasks/math/do/district_rankings_calc/2020ne")
    assert resp.status_code == 200

    district = District.get_by_id("2020ne")
    assert district is not None
    assert district.advancement_cutoffs == {
        "dcmp_original": 36,
        "dcmp_effective": 35,
        "dcmp_declines": ["frc10"],
        "cmp_original": 0,
        "cmp_effective": 0,
        "cmp_declines": [],
        "cmp_qualification": {},
    }


@mock.patch.object(DistrictHelper, "calculate_rankings")
def test_calc_carries_forward_cmp_cutoffs(
    calc_mock: mock.Mock, tasks_client: Client
) -> None:
    district = District(id="2020ne", year=2020, abbreviation="ne")
    district.advancement_cutoffs = DistrictAdvancementCutoffs(
        dcmp_original=0,
        dcmp_effective=0,
        dcmp_declines=[],
        cmp_original=190,
        cmp_effective=173,
        cmp_declines=["frc95"],
        cmp_qualification={"frc95": CmpQualificationMethod.DISTRICT_POINTS},
    )
    district.put()
    qual_event = Event(
        id="2020ndis", year=2020, event_short="ndis", event_type_enum=EventType.DISTRICT
    )
    dcmp_event = Event(
        id="2020necmp",
        year=2020,
        event_short="necmp",
        event_type_enum=EventType.DISTRICT_CMP,
    )
    calc_mock.return_value = {
        f"frc{i}": _team_total(qual_event, 100 - i, dcmp_event, 5) for i in range(1, 5)
    }

    resp = tasks_client.get("/tasks/math/do/district_rankings_calc/2020ne")
    assert resp.status_code == 200

    district = District.get_by_id("2020ne")
    assert district is not None
    cutoffs = none_throws(district.advancement_cutoffs)
    assert cutoffs["cmp_original"] == 190
    assert cutoffs["cmp_effective"] == 173
    assert cutoffs["cmp_declines"] == ["frc95"]
    assert cutoffs["cmp_qualification"] == {
        "frc95": CmpQualificationMethod.DISTRICT_POINTS
    }


@mock.patch.object(DistrictHelper, "calculate_rankings")
def test_calc_skips_cutoffs_when_dcmp_award_only(
    calc_mock: mock.Mock, tasks_client: Client
) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()
    qual_event = Event(
        id="2020ndis", year=2020, event_short="ndis", event_type_enum=EventType.DISTRICT
    )
    dcmp_event = Event(
        id="2020necmp",
        year=2020,
        event_short="necmp",
        event_type_enum=EventType.DISTRICT_CMP,
    )
    calc_mock.return_value = {
        "frc254": _team_total(qual_event, 50, dcmp_event, 0, dcmp_award_points=24)
    }

    resp = tasks_client.get("/tasks/math/do/district_rankings_calc/2020ne")
    assert resp.status_code == 200

    district = District.get_by_id("2020ne")
    assert district is not None
    assert district.advancement_cutoffs is None


@mock.patch.object(DistrictHelper, "calculate_rankings")
def test_calc_with_adjustments(calc_mock: mock.Mock, tasks_client: Client) -> None:
    District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
        adjustments={"frc254": 5},
    ).put()
    calc_mock.return_value = {
        "frc254": DistrictRankingTeamTotal(
            event_points=[],
            point_total=5,
            tiebreakers=[],
            match_scores=[],
            rookie_bonus=0,
            single_event_bonus=0,
            other_bonus=0,
            adjustments=5,
        )
    }

    resp = tasks_client.get(
        "/tasks/math/do/district_rankings_calc/2020ne",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert resp.data == b""

    calc_mock.assert_called_once_with(
        mock.ANY, mock.ANY, mock.ANY, adjustments={"frc254": 5}
    )

    district = District.get_by_id("2020ne")
    assert district is not None
    assert district.rankings[0]["adjustments"] == 5
