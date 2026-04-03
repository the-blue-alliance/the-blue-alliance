import json
from unittest.mock import MagicMock, patch

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.sitevars.s3_export_config import ContentType, S3ExportConfig


def _enable_export() -> None:
    S3ExportConfig.put(
        ContentType(
            aws_access_key="test-key",
            aws_secret_key="test-secret",
            s3_bucket_name="test-bucket",
            export_enabled=True,
        )
    )


def _seed_match(year: int = 2024) -> None:
    event = Event(
        id=f"{year}test",
        year=year,
        event_short="test",
        event_type_enum=0,
    )
    event.put()

    match = Match(
        id=f"{year}test_qm1",
        event=ndb.Key(Event, f"{year}test"),
        year=year,
        comp_level="qm",
        set_number=1,
        match_number=1,
        alliances_json=json.dumps(
            {
                "red": {"teams": ["frc27"], "score": 100},
                "blue": {"teams": ["frc254"], "score": 90},
            }
        ),
        team_key_names=["frc27", "frc254"],
    )
    match.put()


def test_dispatch_disabled(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/enqueue/parquet_export/dispatch")
    assert resp.status_code == 200
    assert b"Export disabled" in resp.data


@patch("backend.tasks_io.handlers.parquet_export.taskqueue")
def test_dispatch_enabled(mock_taskqueue: MagicMock, tasks_client: Client) -> None:
    _enable_export()
    resp = tasks_client.get("/tasks/enqueue/parquet_export/dispatch")
    assert resp.status_code == 200
    assert mock_taskqueue.add.call_count > 0


def test_export_matches_disabled(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/do/parquet_export/matches/2024")
    assert resp.status_code == 200
    assert b"Export disabled" in resp.data


@patch("backend.tasks_io.handlers.parquet_export._upload_parquet")
def test_export_matches(mock_upload: MagicMock, tasks_client: Client) -> None:
    _enable_export()
    _seed_match(2024)

    resp = tasks_client.get("/tasks/do/parquet_export/matches/2024")
    assert resp.status_code == 200

    mock_upload.assert_called_once()
    table = mock_upload.call_args[0][0]
    s3_path = mock_upload.call_args[0][1]
    assert table.num_rows == 1
    assert s3_path == "matches/year=2024/data.parquet"


@patch("backend.tasks_io.handlers.parquet_export._upload_parquet")
def test_export_matches_empty_year(mock_upload: MagicMock, tasks_client: Client) -> None:
    _enable_export()

    resp = tasks_client.get("/tasks/do/parquet_export/matches/1995")
    assert resp.status_code == 200

    mock_upload.assert_called_once()
    table = mock_upload.call_args[0][0]
    assert table.num_rows == 0


@patch("backend.tasks_io.handlers.parquet_export._upload_parquet")
def test_export_teams(mock_upload: MagicMock, tasks_client: Client) -> None:
    _enable_export()
    Team(id="frc27", team_number=27).put()
    Team(id="frc254", team_number=254).put()

    resp = tasks_client.get("/tasks/do/parquet_export/teams")
    assert resp.status_code == 200

    mock_upload.assert_called_once()
    table = mock_upload.call_args[0][0]
    s3_path = mock_upload.call_args[0][1]
    assert table.num_rows == 2
    assert s3_path == "teams/data.parquet"
