from datetime import datetime
from unittest.mock import patch

from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.event_predictions_v2 import EventPredictionsV2
from backend.common.models.match import Match
from backend.common.models.prediction_state import SeasonPredictionState


def test_advance_season_predictions_no_matches(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/tasks/math/do/season_predictions_advance/2024")
    assert resp.status_code == 200
    assert b"No played matches found" in resp.data


def test_advance_season_predictions_and_project(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2024casj",
        year=2024,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    now = datetime(2024, 3, 30, 14, 0)

    Match(
        id="2024casj_qm1",
        year=2024,
        event=ndb.Key(Event, "2024casj"),
        match_number=1,
        set_number=1,
        comp_level="qm",
        team_key_names=["frc254", "frc1678", "frc971", "frc118", "frc148", "frc33"],
        time=now,
        actual_time=now,
        alliances_json='{"red": {"score": 85, "teams": ["frc254", "frc1678", "frc971"]}, "blue": {"score": 72, "teams": ["frc118", "frc148", "frc33"]}}',
        score_breakdown_json='{"red": {"melodyBonusAchieved": true, "ensembleBonusAchieved": false, "rp": 3}, "blue": {"melodyBonusAchieved": false, "ensembleBonusAchieved": false, "rp": 0}}',
    ).put()

    Match(
        id="2024casj_qm2",
        year=2024,
        event=ndb.Key(Event, "2024casj"),
        match_number=2,
        set_number=1,
        comp_level="qm",
        team_key_names=["frc254", "frc118", "frc971", "frc1678", "frc148", "frc33"],
        time=now,
        alliances_json='{"red": {"score": -1, "teams": ["frc254", "frc118", "frc971"]}, "blue": {"score": -1, "teams": ["frc1678", "frc148", "frc33"]}}',
    ).put()

    mock_storage: dict[str, bytes] = {}

    def fake_write(
        file_name, content, content_type="text/plain", bucket=None, metadata=None
    ):
        mock_storage[file_name] = content

    def fake_read(file_name, bucket=None):
        return mock_storage.get(file_name)

    with (
        patch("backend.common.storage.write", side_effect=fake_write),
        patch("backend.common.storage.read", side_effect=fake_read),
    ):
        # 1. Advance Season
        resp = tasks_cpu_client.get("/tasks/math/do/season_predictions_advance/2024")
        assert resp.status_code == 200
        assert b"Advanced 1 matches" in resp.data

        # Verify SeasonPredictionState metadata
        state = SeasonPredictionState.get_by_id("2024")
        assert state is not None
        assert state.match_count == 1
        assert state.last_match_key == "2024casj_qm1"
        assert "predictions/2024/state_active.bin.gz" in mock_storage

        # Verify task enqueued
        tasks = taskqueue_stub.get_filtered_tasks(
            queue_names="event-predictions-project"
        )
        assert len(tasks) == 1
        assert tasks[0].url == "/tasks/math/do/event_predictions_project/2024casj"

        # 2. Project Event Predictions
        proj_resp = tasks_cpu_client.get(tasks[0].url)
        assert proj_resp.status_code == 200

        # Verify EventPredictionsV2 entity created
        event_preds = EventPredictionsV2.get_by_id("2024casj")
        assert event_preds is not None
        assert event_preds.as_of_match == "2024casj_qm1"
        payload = event_preds.predictions
        assert payload["model_version"] == "hkf_ev_pcg_v1.0"
        assert "2024casj_qm1" in payload["matches"]
        assert "2024casj_qm2" in payload["matches"]
        qm2_pred = payload["matches"]["2024casj_qm2"]
        assert 0.0 <= qm2_pred["red_win_prob"] <= 1.0
        assert qm2_pred["red"]["mean"] > 0
        assert qm2_pred["blue"]["mean"] > 0
        assert "frc254" in payload["team_ratings"]

        # 3. Idempotent check
        idem_resp = tasks_cpu_client.get(
            "/tasks/math/do/season_predictions_advance/2024"
        )
        assert idem_resp.status_code == 200
        assert b"All played matches already processed" in idem_resp.data

        # 4. Out-of-order match insertion triggering rewind
        # Now finalize Match 2
        qm2 = Match.get_by_id("2024casj_qm2")
        assert qm2 is not None
        qm2.alliances_json = '{"red": {"score": 90, "teams": ["frc254", "frc118", "frc971"]}, "blue": {"score": 65, "teams": ["frc1678", "frc148", "frc33"]}}'
        qm2.put()

        rewind_resp = tasks_cpu_client.get(
            "/tasks/math/do/season_predictions_advance/2024"
        )
        assert rewind_resp.status_code == 200
        assert b"Advanced 2 matches" in rewind_resp.data

        updated_state = SeasonPredictionState.get_by_id("2024")
        assert updated_state is not None
        assert updated_state.match_count == 2
        assert "2024casj_qm2" in updated_state.processed_match_keys_json
