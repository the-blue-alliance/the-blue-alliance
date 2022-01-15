from datetime import datetime
from typing import Tuple
from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.helpers.event_insights_helper import EventInsightsHelper
from backend.common.helpers.matchstats_helper import MatchstatsHelper
from backend.common.helpers.prediction_helper import PredictionHelper
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_insights import EventInsights
from backend.common.models.event_predictions import (
    EventPredictions,
    TEventStatMeanVars,
    TMatchPredictions,
    TMatchPredictionStats,
    TRankingPredictions,
    TRankingPredictionStats,
)
from backend.common.models.stats import EventMatchStats, StatType


def test_enqueue_bad_year(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/event_matchstats/asdf")
    assert resp.status_code == 404


@freeze_time("2020-4-1")
def test_enqueue_no_events(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/event_matchstats/2020")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_enqueue_event(
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    Event(
        id="2020event",
        year=2020,
        event_short="event",
        event_type_enum=EventType.REGIONAL,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/event_matchstats/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="run-in-order")
    assert len(tasks) == 1


@freeze_time("2020-4-1")
def test_enqueue_event_current(
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    Event(
        id="2020event",
        year=2020,
        event_short="event",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime(2020, 4, 1),
        end_date=datetime(2020, 4, 1),
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/event_matchstats/now")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="run-in-order")
    assert len(tasks) == 1


def test_calc_no_event(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/do/event_matchstats/2020test")
    assert resp.status_code == 404


@mock.patch.object(EventInsightsHelper, "calculate_event_insights")
@mock.patch.object(PredictionHelper, "get_ranking_predictions")
@mock.patch.object(PredictionHelper, "get_match_predictions")
@mock.patch.object(MatchstatsHelper, "calculate_matchstats")
def test_calc_matchstats(
    matchstats_mock: mock.Mock,
    match_prediction_mock: mock.Mock,
    ranking_prediction_mock: mock.Mock,
    event_insights_mock: mock.Mock,
    tasks_client: Client,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    matchstats: EventMatchStats = {
        StatType.OPR: {"254": 100.0},
    }
    match_predictions: Tuple[
        TMatchPredictions,
        TMatchPredictionStats,
        TEventStatMeanVars,
    ] = (
        {},
        {},
        {},
    )
    ranking_predictions: Tuple[TRankingPredictions, TRankingPredictionStats] = (
        [],
        {"last_played_match": None},
    )
    event_insights = EventInsights(
        qual=None,
        playoff=None,
    )
    matchstats_mock.return_value = matchstats
    match_prediction_mock.return_value = match_predictions
    ranking_prediction_mock.return_value = ranking_predictions
    event_insights_mock.return_value = event_insights

    resp = tasks_client.get("/tasks/math/do/event_matchstats/2020test")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    ed = EventDetails.get_by_id("2020test")
    assert ed is not None
    assert ed.matchstats == matchstats
    assert ed.predictions == EventPredictions(
        match_predictions=match_predictions[0],
        match_prediction_stats=match_predictions[1],
        stat_mean_vars=match_predictions[2],
        ranking_predictions=ranking_predictions[0],
        ranking_prediction_stats=ranking_predictions[1],
    )
    assert ed.insights == event_insights


@mock.patch.object(EventInsightsHelper, "calculate_event_insights")
@mock.patch.object(PredictionHelper, "get_ranking_predictions")
@mock.patch.object(PredictionHelper, "get_match_predictions")
@mock.patch.object(MatchstatsHelper, "calculate_matchstats")
def test_calc_matchstats_no_output_in_taskqueue(
    matchstats_mock: mock.Mock,
    match_prediction_mock: mock.Mock,
    ranking_prediction_mock: mock.Mock,
    event_insights_mock: mock.Mock,
    tasks_client: Client,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    matchstats: EventMatchStats = {
        StatType.OPR: {"254": 100.0},
    }
    match_predictions: Tuple[
        TMatchPredictions,
        TMatchPredictionStats,
        TEventStatMeanVars,
    ] = (
        {},
        {},
        {},
    )
    ranking_predictions: Tuple[TRankingPredictions, TRankingPredictionStats] = (
        [],
        {"last_played_match": None},
    )
    event_insights = EventInsights(
        qual=None,
        playoff=None,
    )
    matchstats_mock.return_value = matchstats
    match_prediction_mock.return_value = match_predictions
    ranking_prediction_mock.return_value = ranking_predictions
    event_insights_mock.return_value = event_insights

    resp = tasks_client.get(
        "/tasks/math/do/event_matchstats/2020test",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0
