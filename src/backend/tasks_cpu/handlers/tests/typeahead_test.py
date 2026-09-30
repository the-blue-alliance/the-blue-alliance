import json
from typing import List

from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.models.typeahead_entry import TypeaheadEntry


def _entry_data(key_name: str) -> List[str]:
    entry = TypeaheadEntry.get_by_id(key_name)
    assert entry is not None
    return json.loads(entry.data_json)


def test_enqueue(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/typeaheadcalc")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks-b2/do/math/typeaheadcalc"
    assert tasks[0].method == "GET"


def test_enqueue_no_output_in_taskqueue(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/typeaheadcalc",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) == 1


def test_do_empty(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/typeaheadcalc")
    assert resp.status_code == 200
    assert b"Calculated typeahead entries!" in resp.data
    assert TypeaheadEntry.query().fetch() == []


def test_do_no_output_in_taskqueue(tasks_cpu_client: Client) -> None:
    Team(id="frc254", team_number=254, nickname="The Cheesy Poofs").put()

    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/typeaheadcalc",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0
    assert _entry_data(TypeaheadEntry.ALL_TEAMS_KEY) == ["254 | The Cheesy Poofs"]


def test_do_teams(tasks_cpu_client: Client) -> None:
    Team(id="frc254", team_number=254, nickname="The Cheesy Poofs").put()
    # Team without a nickname falls back to "Team <number>"
    Team(id="frc1", team_number=1).put()
    Team(id="frc1114", team_number=1114, nickname="Simbotics").put()

    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/typeaheadcalc")
    assert resp.status_code == 200

    # Ordered by team number
    assert _entry_data(TypeaheadEntry.ALL_TEAMS_KEY) == [
        "1 | Team 1",
        "254 | The Cheesy Poofs",
        "1114 | Simbotics",
    ]
    assert TypeaheadEntry.get_by_id(TypeaheadEntry.ALL_EVENTS_KEY) is None
    assert TypeaheadEntry.get_by_id(TypeaheadEntry.ALL_DISTRICTS_KEY) is None


def test_do_districts(tasks_cpu_client: Client) -> None:
    District(id="2020fim", year=2020, abbreviation="fim", display_name="Michigan").put()
    District(id="2019fim", year=2019, abbreviation="fim", display_name="Michigan").put()
    District(
        id="2020ne", year=2020, abbreviation="ne", display_name="New England"
    ).put()

    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/typeaheadcalc")
    assert resp.status_code == 200

    # Duplicate names across years are collapsed into one entry
    assert _entry_data(TypeaheadEntry.ALL_DISTRICTS_KEY) == [
        "Michigan District [FIM]",
        "New England District [NE]",
    ]
    assert TypeaheadEntry.get_by_id(TypeaheadEntry.ALL_TEAMS_KEY) is None
    assert TypeaheadEntry.get_by_id(TypeaheadEntry.ALL_EVENTS_KEY) is None


def test_do_districts_without_display_name_uses_render_name(
    tasks_cpu_client: Client,
) -> None:
    """Bug #10840-c: a district with no display name should be labelled with
    `District.render_name` (its abbreviation), not "None"."""
    District(id="2020ont", year=2020, abbreviation="ont").put()

    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/typeaheadcalc")
    assert resp.status_code == 200

    assert _entry_data(TypeaheadEntry.ALL_DISTRICTS_KEY) == ["ONT District [ONT]"]


def test_do_events(tasks_cpu_client: Client) -> None:
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        name="Silicon Valley Regional",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        name="New York City Regional",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        name="Silicon Valley Regional",
        event_type_enum=EventType.REGIONAL,
    ).put()

    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/typeaheadcalc")
    assert resp.status_code == 200

    # Ordered by year descending, then name
    assert _entry_data(TypeaheadEntry.ALL_EVENTS_KEY) == [
        "2020 New York City Regional [NYNY]",
        "2020 Silicon Valley Regional [CASJ]",
        "2019 Silicon Valley Regional [CASJ]",
    ]
    assert _entry_data(TypeaheadEntry.YEAR_EVENTS_KEY.format(2020)) == [
        "2020 New York City Regional [NYNY]",
        "2020 Silicon Valley Regional [CASJ]",
    ]
    assert _entry_data(TypeaheadEntry.YEAR_EVENTS_KEY.format(2019)) == [
        "2019 Silicon Valley Regional [CASJ]",
    ]
    assert TypeaheadEntry.get_by_id(TypeaheadEntry.ALL_TEAMS_KEY) is None
    assert TypeaheadEntry.get_by_id(TypeaheadEntry.ALL_DISTRICTS_KEY) is None


def test_do_removes_stale_entries(tasks_cpu_client: Client) -> None:
    # Pre-existing entries for data that no longer exists get deleted,
    # while entries that are recomputed get overwritten.
    TypeaheadEntry(id=TypeaheadEntry.YEAR_EVENTS_KEY.format(2010), data_json="[]").put()
    TypeaheadEntry(id=TypeaheadEntry.ALL_TEAMS_KEY, data_json='["old"]').put()
    Team(id="frc254", team_number=254, nickname="The Cheesy Poofs").put()

    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/typeaheadcalc")
    assert resp.status_code == 200

    assert TypeaheadEntry.get_by_id(TypeaheadEntry.YEAR_EVENTS_KEY.format(2010)) is None
    assert _entry_data(TypeaheadEntry.ALL_TEAMS_KEY) == ["254 | The Cheesy Poofs"]
    assert {k.id() for k in TypeaheadEntry.query().fetch(keys_only=True)} == {
        TypeaheadEntry.ALL_TEAMS_KEY
    }
