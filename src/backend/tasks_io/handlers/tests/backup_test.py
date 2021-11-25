import pytest
import json
from datetime import date
from unittest.mock import patch

from flask.testing import FlaskClient
from google.cloud import ndb

from backend.common import storage
from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.alliance import EventAlliance, MatchAlliance
from backend.common.models.award import Award
from backend.common.models.award_recipient import AwardRecipient
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_ranking import EventRanking
from backend.common.models.event_team import EventTeam
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo
from backend.common.models.team import Team


@pytest.fixture()
def test_event(ndb_client):
    with ndb_client.context():
        event = Event(
            id="2012migl",
            name="Kettering but in 2012",
            event_short="migl",
            year=2012,
            event_type_enum=EventType.DISTRICT,
        )
        event.put()
        return event


def test_enqueue(taskqueue_stub, tasks_io_client: FlaskClient):
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backups")
    assert len(tasks) == 0

    response = tasks_io_client.get("/backup/enqueue")
    assert response.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backups")
    assert len(tasks) == 2

    events_task = tasks[0]
    assert events_task.url == "/backup/events"
    assert events_task.method == "GET"
    assert events_task.payload is None

    teams_task = tasks[1]
    assert teams_task.url == "/backup/teams"
    assert teams_task.method == "GET"
    assert teams_task.payload is None


def test_backup_events_all(taskqueue_stub, tasks_io_client: FlaskClient):
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backups")
    assert len(tasks) == 0

    # Mock our SeasonHelper.get_valid_years so our # of tasks is always the same
    valid_years = list(range(1992, date.today().year))
    with patch.object(SeasonHelper, "get_valid_years", return_value=valid_years):
        response = tasks_io_client.get("/backup/events")

    assert response.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backups")
    assert len(tasks) == len(valid_years)

    for year, task in zip(valid_years, tasks):
        assert task.url == f"/backup/events/{year}"
        assert task.method == "GET"
        assert task.payload is None


def test_backup_events_year_no_events(taskqueue_stub, tasks_io_client: FlaskClient):
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backups")
    assert len(tasks) == 0

    response = tasks_io_client.get("/backup/events/2012")
    assert response.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backups")
    assert len(tasks) == 0


def test_backup_events_year(test_event, taskqueue_stub, tasks_io_client: FlaskClient):
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backups")
    assert len(tasks) == 0

    response = tasks_io_client.get("/backup/events/2012")
    assert response.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backups")
    assert len(tasks) == 1

    task = tasks[0]
    assert task.url == f"/backup/event/2012migl"
    assert task.method == "GET"
    assert task.payload is None


def test_backup_event_no_event(tasks_io_client: FlaskClient):
    response = tasks_io_client.get("/backup/event/2012migl")
    assert response.status_code == 404


def test_backup_event_empty_event(test_event, tasks_io_client: FlaskClient):
    with patch.object(storage, "write") as mock_write:
        response = tasks_io_client.get("/backup/event/2012migl")

    assert response.status_code == 200

    mock_write.assert_not_called()


def test_backup_event_awards(test_event, ndb_client, tasks_io_client: FlaskClient):
    with ndb_client.context():
        recipients = []
        Award(
            id=f"{test_event.key_name}_0",
            year=test_event.year,
            award_type_enum=AwardType.CHAIRMANS,
            event_type_enum=EventType.DISTRICT,
            event=test_event.key,
            name_str="Chairmans Award",
            recipient_json_list=[json.dumps(AwardRecipient(awardee=None, team_number=7332))],
        ).put()
        Award(
            id=f"{test_event.key_name}_1",
            year=test_event.year,
            award_type_enum=AwardType.WINNER,
            event_type_enum=EventType.DISTRICT,
            event=test_event.key,
            name_str="Winner",
            recipient_json_list=[json.dumps(r) for r in [AwardRecipient(awardee=None, team_number=1), AwardRecipient(awardee=None, team_number=2), AwardRecipient(awardee=None, team_number=3)]],
        ).put()

    with patch.object(storage, "write") as mock_write:
        response = tasks_io_client.get("/backup/event/2012migl")

    assert response.status_code == 200

    # Should be ID, name, recipient
    expected_data = "2012migl_0,Chairmans Award,frc7332,\r\n2012migl_1,Winner,frc1,\r\n2012migl_1,Winner,frc2,\r\n2012migl_1,Winner,frc3,\r\n"

    mock_write.assert_called_once_with("tba-data-backup/events/2012/2012migl/2012migl_awards.csv", expected_data)


def test_backup_event_matches(test_event, ndb_client, tasks_io_client: FlaskClient):
    with ndb_client.context():
        Match(
            id=f"{test_event.key_name}_qm1",
            event=test_event.key,
            year=test_event.year,
            comp_level=CompLevel.QM,
            set_number=1,
            match_number=1,
            alliances_json=json.dumps(
                {
                    AllianceColor.RED: MatchAlliance(
                        teams=["frc1", "frc2", "frc3"], score=5
                    ),
                    AllianceColor.BLUE: MatchAlliance(
                        teams=["frc4", "frc5", "frc6"], score=10
                    ),
                }
            )
        ).put()
        Match(
            id=f"{test_event.key_name}_qm2",
            event=test_event.key,
            year=test_event.year,
            comp_level=CompLevel.QM,
            set_number=1,
            match_number=2,
            alliances_json=json.dumps(
                {
                    AllianceColor.RED: MatchAlliance(
                        teams=["frc1", "frc2", "frc3"], score=15
                    ),
                    AllianceColor.BLUE: MatchAlliance(
                        teams=["frc4", "frc5", "frc6"], score=20
                    ),
                }
            )
        ).put()

    with patch.object(storage, "write") as mock_write:
        response = tasks_io_client.get("/backup/event/2012migl")

    assert response.status_code == 200

    # key, red, blue, red score, blue score
    expected_data = "2012migl_qm1,frc1,frc2,frc3,frc4,frc5,frc6,5,10\r\n2012migl_qm2,frc1,frc2,frc3,frc4,frc5,frc6,15,20\r\n"

    mock_write.assert_called_once_with("tba-data-backup/events/2012/2012migl/2012migl_matches.csv", expected_data)


def test_backup_event_teams(test_event, ndb_client, tasks_io_client: FlaskClient):
    team_numbers = [1, 2, 7332]
    with ndb_client.context():
        for team_number in team_numbers:
            team = Team(
                id=f"frc{team_number}",
                team_number=team_number,
            )
            team.put()

            EventTeam(
                id=f"{test_event.key_name}_{team.key.string_id()}",
                event=test_event.key,
                team=team.key,
                year=2012,
            ).put()

    with patch.object(storage, "write") as mock_write:
        response = tasks_io_client.get("/backup/event/2012migl")

    assert response.status_code == 200

    team_number_strings = [f"frc{tn}" for tn in team_numbers]
    expected_data = f"{','.join(team_number_strings)}\r\n"

    mock_write.assert_called_once_with("tba-data-backup/events/2012/2012migl/2012migl_teams.csv", expected_data)


def test_backup_event_rankings(test_event, ndb_client, tasks_io_client: FlaskClient):
    with ndb_client.context():
        EventDetails(
            id=test_event.key_name,
            rankings2=[
                EventRanking(
                    rank=1,
                    team_key="frc1",
                    record=WLTRecord(
                        wins=1,
                        losses=0,
                        ties=0,
                    ),
                    qual_average=None,
                    matches_played=1,
                    dq=0,
                    sort_orders=[0, 0, 0, 0, 0],
                ),
                EventRanking(
                    rank=2,
                    team_key="frc2",
                    record=WLTRecord(
                        wins=0,
                        losses=1,
                        ties=0,
                    ),
                    qual_average=None,
                    matches_played=2,
                    dq=0,
                    sort_orders=[0, 0, 0, 0, 0],
                ),
                EventRanking(
                    rank=3,
                    team_key="frc3",
                    record=WLTRecord(
                        wins=0,
                        losses=0,
                        ties=1,
                    ),
                    qual_average=None,
                    matches_played=3,
                    dq=0,
                    sort_orders=[0, 0, 0, 0, 0],
                )
            ]
        ).put()

    with patch.object(storage, "write") as mock_write:
        response = tasks_io_client.get("/backup/event/2012migl")

    assert response.status_code == 200

    # key, red, blue, red score, blue score
    expected_data = "frc1,frc2,frc7332\r\n"

    mock_write.assert_called_once_with("tba-data-backup/events/2012/2012migl/2012migl_rankings.csv", expected_data)


def test_backup_event_alliances(test_event, ndb_client, tasks_io_client: FlaskClient):
    with ndb_client.context():
        alliances = [
            EventAlliance(picks=["frc1", "frc2", "frc3"]),
            EventAlliance(picks=["frc4", "frc5", "frc6"]),
        ]
        EventDetails(
            id=test_event.key_name,
            alliance_selections=alliances,
        ).put()

    with patch.object(storage, "write") as mock_write:
        response = tasks_io_client.get("/backup/event/2012migl")

    assert response.status_code == 200

    # key, red, blue, red score, blue score
    expected_data = "frc1,frc2,frc3\r\nfrc4,frc5,frc6\r\n"

    mock_write.assert_called_once_with("tba-data-backup/events/2012/2012migl/2012migl_alliances.csv", expected_data)
