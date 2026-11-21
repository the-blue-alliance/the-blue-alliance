import json
from datetime import datetime
from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.match_time_prediction_helper import (
    MatchTimePredictionHelper,
)
from backend.common.memcache_models.event_nexus_queue_status_memcache import (
    EventNexusQueueStatusMemcache,
)
from backend.common.models.alliance import MatchAlliance
from backend.common.models.event import Event
from backend.common.models.event_queue_status import (
    EventQueueStatus,
    NexusMatch,
    NexusMatchStatus,
    NexusMatchTiming,
)
from backend.common.models.match import Match
from backend.common.sitevars.apistatus_down_events import ApiStatusDownEvents


def test_enqueue_playoff_advancement_no_events(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/predict_match_times")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@freeze_time("2020-4-1")
def test_enqueue_playoff_advancement(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime(2020, 4, 1),
        end_date=datetime(2020, 4, 1),
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/predict_match_times")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued time prediction for 1 events"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1


@freeze_time("2020-4-1")
def test_enqueue_playoff_advancement_clears_down_events(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    ApiStatusDownEvents.put(["2020old"])
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime(2020, 4, 1),
        end_date=datetime(2020, 4, 1),
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/predict_match_times")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued time prediction for 1 events"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1

    assert ApiStatusDownEvents.get() == []


def test_do_predictions_no_event(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/do/predict_match_times/2020test")
    assert resp.status_code == 404


@mock.patch.object(MatchTimePredictionHelper, "predict_future_matches")
def test_do_predictions_no_matches(
    predict_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()

    resp = tasks_client.get("/tasks/math/do/predict_match_times/2020test")
    assert resp.status_code == 200

    predict_mock.assert_not_called()


@mock.patch.object(MatchTimePredictionHelper, "predict_future_matches")
def test_do_predictions(
    predict_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        timezone_id="America/New_York",
    ).put()
    Match(
        id="2020test_qm1",
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        event=ndb.Key(Event, "2020test"),
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(teams=[], score=-1),
                AllianceColor.BLUE: MatchAlliance(teams=[], score=-1),
            }
        ),
    ).put()

    resp = tasks_client.get("/tasks/math/do/predict_match_times/2020test")
    assert resp.status_code == 200

    predict_mock.assert_called_once()


@freeze_time("2020-4-1 09:30")
@mock.patch.object(MatchTimePredictionHelper, "predict_future_matches")
def test_do_predictions_mark_event_down(
    predict_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        timezone_id="America/New_York",
    ).put()
    Match(
        id="2020test_qm1",
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        event=ndb.Key(Event, "2020test"),
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(teams=[], score=1),
                AllianceColor.BLUE: MatchAlliance(teams=[], score=0),
            }
        ),
        actual_time=datetime(2020, 4, 1, 9, 0),
    ).put()
    Match(
        id="2020test_qm2",
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        event=ndb.Key(Event, "2020test"),
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(teams=[], score=-1),
                AllianceColor.BLUE: MatchAlliance(teams=[], score=-1),
            }
        ),
        time=datetime(2020, 4, 1, 9, 5),
        predicted_time=datetime(2020, 4, 1, 9, 45),
    ).put()

    # We have at least one played match, and at least 30m past the predicted
    # time of the next unplayed match.
    resp = tasks_client.get("/tasks/math/do/predict_match_times/2020test")
    assert resp.status_code == 200

    assert ApiStatusDownEvents.get() == ["2020test"]


@freeze_time("2020-4-1 09:30")
@mock.patch.object(MatchTimePredictionHelper, "predict_future_matches")
def test_do_predictions_mark_event_up(
    predict_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        timezone_id="America/New_York",
    ).put()
    Match(
        id="2020test_qm1",
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        event=ndb.Key(Event, "2020test"),
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(teams=[], score=1),
                AllianceColor.BLUE: MatchAlliance(teams=[], score=0),
            }
        ),
        actual_time=datetime(2020, 4, 1, 9, 0),
    ).put()
    ApiStatusDownEvents.put(["2020test"])

    # We have at least one played match, and at least 30m past the predicted
    # time of the next unplayed match.
    resp = tasks_client.get("/tasks/math/do/predict_match_times/2020test")
    assert resp.status_code == 200

    assert ApiStatusDownEvents.get() == []


def _put_played_and_unplayed_matches() -> None:
    Match(
        id="2020test_qm1",
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        event=ndb.Key(Event, "2020test"),
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(teams=[], score=1),
                AllianceColor.BLUE: MatchAlliance(teams=[], score=0),
            }
        ),
        actual_time=datetime(2020, 4, 1, 9, 0),
    ).put()
    Match(
        id="2020test_qm2",
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=2,
        event=ndb.Key(Event, "2020test"),
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(teams=[], score=-1),
                AllianceColor.BLUE: MatchAlliance(teams=[], score=-1),
            }
        ),
        time=datetime(2020, 4, 1, 9, 5),
        predicted_time=datetime(2020, 4, 1, 9, 10),
    ).put()


def _nexus_status(most_recent_match_status: NexusMatchStatus) -> EventQueueStatus:
    return EventQueueStatus(
        data_as_of_ms=0,
        now_queueing=None,
        matches={
            "2020test_qm1": NexusMatch(
                label="Quals 1",
                status=most_recent_match_status,
                played=True,
                times=NexusMatchTiming(
                    estimated_queue_time_ms=None, estimated_start_time_ms=None
                ),
            ),
            "2020test_qm2": NexusMatch(
                label="Quals 2",
                status=NexusMatchStatus.ON_DECK,
                played=False,
                times=NexusMatchTiming(
                    estimated_queue_time_ms=None, estimated_start_time_ms=None
                ),
            ),
        },
    )


@freeze_time("2020-4-1 09:30")
@mock.patch.object(MatchTimePredictionHelper, "predict_future_matches")
def test_do_predictions_uses_nexus_data_when_last_match_on_field(
    predict_mock: mock.Mock,
    tasks_client: Client,
    memcache_stub: testbed.memcache_stub.MemcacheServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        timezone_id="America/New_York",
    ).put()
    _put_played_and_unplayed_matches()
    status = _nexus_status(NexusMatchStatus.ON_FIELD)
    EventNexusQueueStatusMemcache("2020test").put(status)

    resp = tasks_client.get("/tasks/math/do/predict_match_times/2020test")
    assert resp.status_code == 200

    predict_mock.assert_called_once()
    assert predict_mock.call_args[0][5] == status


@freeze_time("2020-4-1 09:30")
@mock.patch.object(MatchTimePredictionHelper, "predict_future_matches")
def test_do_predictions_ignores_stale_nexus_data(
    predict_mock: mock.Mock,
    tasks_client: Client,
    memcache_stub: testbed.memcache_stub.MemcacheServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        timezone_id="America/New_York",
    ).put()
    _put_played_and_unplayed_matches()
    # The most recently played match is not "on field" according to Nexus, so
    # the queue data is considered stale and must not be passed to the predictor
    EventNexusQueueStatusMemcache("2020test").put(
        _nexus_status(NexusMatchStatus.NOW_QUEUING)
    )

    resp = tasks_client.get("/tasks/math/do/predict_match_times/2020test")
    assert resp.status_code == 200

    predict_mock.assert_called_once()
    assert predict_mock.call_args[0][5] is None


@freeze_time("2020-4-1 09:30")
@mock.patch.object(MatchTimePredictionHelper, "predict_future_matches")
def test_do_predictions_no_output_in_taskqueue(
    predict_mock: mock.Mock,
    tasks_client: Client,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        timezone_id="America/New_York",
    ).put()
    _put_played_and_unplayed_matches()

    resp = tasks_client.get(
        "/tasks/math/do/predict_match_times/2020test",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert resp.data == b""

    predict_mock.assert_called_once()
    assert ApiStatusDownEvents.get() == []
