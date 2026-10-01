import pytest
from freezegun import freeze_time
from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.consts.insight_type import InsightType
from backend.common.consts.renamed_districts import RenamedDistricts
from backend.common.helpers.insights_helper_utils import create_insight
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.district import District
from backend.common.models.insight import Insight
from backend.common.models.insight_v2 import InsightV2


def test_enqueue_bad_kind(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/asdf/2023")
    assert resp.status_code == 404


def test_enqueue_bad_year(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/matches/asdf")
    assert resp.status_code == 404


def test_enqueue(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/matches/2023")
    assert resp.status_code == 200

    tasks = tasks_cpu_client = taskqueue_stub.get_filtered_tasks(
        queue_names="backend-tasks"
    )
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks-b2/do/math/insights/matches/2023"


def test_enqueue_no_output_in_taskqueue(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/matches/2023",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


@freeze_time("2020-04-01")
def test_enqueue_defaults_to_current_season(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/matches")
    assert resp.status_code == 200

    tasks = tasks_cpu_client = taskqueue_stub.get_filtered_tasks(
        queue_names="backend-tasks"
    )
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks-b2/do/math/insights/matches/2020"


def test_do_bad_kind(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/asdf/2023")
    assert resp.status_code == 404


def test_do_bad_year(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/matches/asdf")
    assert resp.status_code == 404


@pytest.mark.parametrize("insight_type", list(InsightType))  # pyre-ignore[6]
def test_calc(tasks_cpu_client: Client, insight_type: InsightType) -> None:
    resp = tasks_cpu_client.get(
        f"/backend-tasks-b2/do/math/insights/{insight_type}/2023"
    )
    assert resp.status_code == 200


def test_calc_no_output_in_taskqueue(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/insights/matches/2023",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_enqueue_district_insights(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    District(id="2026fim", year=2026, abbreviation="fim").put()
    District(id="2026ne", year=2026, abbreviation="ne").put()

    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/districts/2026"
    )
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) == 2
    for task in tasks:
        assert task.url.startswith("/backend-tasks-b2/do/math/insights/districts/2026/")


@freeze_time("2026-03-01")
def test_enqueue_district_insights_defaults_to_current_season(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    District(id="2026fim", year=2026, abbreviation="fim").put()

    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/districts")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) == 1
    for task in tasks:
        assert task.url.startswith("/backend-tasks-b2/do/math/insights/districts/2026/")


def test_enqueue_district_insights_no_output_in_taskqueue(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/districts",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_enqueue_district_insights_year_zero(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    from backend.common.consts.renamed_districts import RenamedDistricts

    expected_abbrevs = set(RenamedDistricts.get_latest_codes())

    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/districts/0")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) == len(expected_abbrevs)
    enqueued_abbrevs = {task.url.split("/")[-1] for task in tasks}
    assert enqueued_abbrevs == expected_abbrevs
    for task in tasks:
        assert task.url.startswith("/backend-tasks-b2/do/math/insights/districts/0/")


def test_enqueue_district_insights_year_zero_no_output_in_taskqueue(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/districts/0",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_do_district_insights_for_abbreviation(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/districts/2026/fim")
    assert resp.status_code == 200


def test_do_district_insights_for_abbreviation_year_zero(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/districts/0/fim")
    assert resp.status_code == 200


def test_do_district_insights_for_abbreviation_no_output_in_taskqueue(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/insights/districts/2026/fim",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_calc_districts_year_zero_writes_overall_district_insights(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/districts/0")
    assert resp.status_code == 200

    # Team data and district data insights for every district abbreviation
    stored = Insight.query().fetch()
    assert len(stored) == 2 * len(RenamedDistricts.get_latest_codes())
    assert {insight.year for insight in stored} == {0}
    assert {insight.district_abbreviation for insight in stored} == set(
        RenamedDistricts.get_latest_codes()
    )


def test_calc_districts_nonzero_year_is_a_noop(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/districts/2023")
    assert resp.status_code == 200
    assert Insight.query().count() == 0


def test_do_leaderboard_unknown_kind(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/insights/leaderboards/asdf/2023"
    )
    assert resp.status_code == 200
    assert resp.data == b"Unknown leaderboard kind asdf"
    assert Insight.query().count() == 0


@pytest.mark.parametrize("kind", ["match", "team", "event"])
def test_do_leaderboard(tasks_cpu_client: Client, kind: str) -> None:
    resp = tasks_cpu_client.get(
        f"/backend-tasks-b2/do/math/insights/leaderboards/{kind}/2023"
    )
    assert resp.status_code == 200

    stored = Insight.query().fetch()
    assert len(stored) > 0
    for insight in stored:
        assert insight.year == 2023
        assert insight.data["key_type"] == kind


def test_enqueue_leaderboard(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/leaderboards/team/2023"
    )
    assert resp.status_code == 200
    assert resp.data == b"enqueued team leaderboard insights for year 2023"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert [task.url for task in tasks] == [
        "/backend-tasks-b2/do/math/insights/leaderboards/team/2023"
    ]


@freeze_time("2020-04-01")
def test_enqueue_leaderboard_defaults_to_current_season(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/leaderboards/match"
    )
    assert resp.status_code == 200
    assert resp.data == b"enqueued match leaderboard insights for year 2020"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert [task.url for task in tasks] == [
        "/backend-tasks-b2/do/math/insights/leaderboards/match/2020"
    ]


@freeze_time("2020-04-01")
def test_enqueue_all_leaderboard_insights(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/leaderboards/event/all"
    )
    assert resp.status_code == 200
    assert resp.data == b"enqueued event leaderboard insights for all years"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    expected_years = list(SeasonHelper.get_valid_years()) + [0]
    assert expected_years[0] == SeasonHelper.MIN_YEAR
    assert expected_years[-2] == 2020
    assert sorted(task.url for task in tasks) == sorted(
        f"/backend-tasks-b2/do/math/insights/leaderboards/event/{year}"
        for year in expected_years
    )


def test_enqueue_notables(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/notables/2023")
    assert resp.status_code == 200
    assert resp.data == b"enqueued notable insights for year 2023"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert [task.url for task in tasks] == ["/backend-tasks-b2/do/math/notables/2023"]


@freeze_time("2020-04-01")
def test_enqueue_notables_defaults_to_current_season(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/notables")
    assert resp.status_code == 200
    assert resp.data == b"enqueued notable insights for year 2020"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert [task.url for task in tasks] == ["/backend-tasks-b2/do/math/notables/2020"]


@freeze_time("2020-04-01")
def test_enqueue_all_notables_insights(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/notables/all")
    assert resp.status_code == 200
    assert resp.data == b"enqueued all notable insights"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    expected_years = list(SeasonHelper.get_valid_years()) + [0]
    assert expected_years[-2] == 2020
    assert sorted(task.url for task in tasks) == sorted(
        f"/backend-tasks-b2/do/math/notables/{year}" for year in expected_years
    )


def test_do_notables(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/notables/2023")
    assert resp.status_code == 200

    stored = Insight.query().fetch()
    assert len(stored) > 0
    for insight in stored:
        assert insight.year == 2023
        assert insight.name.startswith("notables_")


def test_enqueue_overall_insights(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/overallinsights/awards")
    assert resp.status_code == 200
    assert b"Enqueued calculation of awards Overall Insights" in resp.data

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert [task.url for task in tasks] == [
        "/backend-tasks-b2/do/math/overallinsights/awards"
    ]


def test_enqueue_overall_insights_no_output_in_taskqueue(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/overallinsights/matches",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")) == 1


def test_do_overall_match_insights(tasks_cpu_client: Client) -> None:
    create_insight(
        data=100, name=Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], year=2023
    ).put()

    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/overallinsights/matches")
    assert resp.status_code == 200
    assert b"Calculated the following Overall Insights for matches" in resp.data
    assert Insight.INSIGHT_NAMES[Insight.NUM_MATCHES].encode() in resp.data

    overall = Insight.get_by_id(
        Insight.render_key_name(0, Insight.INSIGHT_NAMES[Insight.NUM_MATCHES])
    )
    assert overall is not None
    assert overall.data == [[2023, 100]]


def test_do_overall_award_insights(tasks_cpu_client: Client) -> None:
    create_insight(
        data=[(2, ["frc254"])],
        name=Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS],
        year=2023,
    ).put()

    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/overallinsights/awards")
    assert resp.status_code == 200
    assert b"Calculated the following Overall Insights for awards" in resp.data

    overall = Insight.get_by_id(
        Insight.render_key_name(0, Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS])
    )
    assert overall is not None
    assert overall.data == [[2, ["frc254"]]]


def test_do_overall_insights_no_output_in_taskqueue(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/overallinsights/matches",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_do_overall_insights_unknown_kind_in_taskqueue_is_a_noop(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/overallinsights/asdf",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0
    assert Insight.query().count() == 0


def test_enqueue_all_insights_of_kind_bad_kind(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/asdf/all")
    assert resp.status_code == 404


@freeze_time("2020-04-01")
def test_enqueue_all_insights_of_kind(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/awards/all")
    assert resp.status_code == 200
    assert b"Enqueued calculation of all insights for type awards" in resp.data

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    expected_years = list(SeasonHelper.get_valid_years())
    assert expected_years[-1] == 2020
    assert sorted(task.url for task in tasks) == sorted(
        f"/backend-tasks-b2/do/math/insights/awards/{year}" for year in expected_years
    )


def test_enqueue_all_insights_of_kind_no_output_in_taskqueue(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/matches/all",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0
    assert len(taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")) == len(
        SeasonHelper.get_valid_years()
    )


def test_enqueue_insights_v2(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights_v2/2024")
    assert resp.status_code == 200
    assert resp.data == b"enqueued insights_v2 for year 2024"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert [task.url for task in tasks] == [
        "/backend-tasks-b2/do/math/insights_v2/2024"
    ]


@freeze_time("2020-04-01")
def test_enqueue_insights_v2_defaults_to_current_season(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights_v2")
    assert resp.status_code == 200
    assert resp.data == b"enqueued insights_v2 for year 2020"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert [task.url for task in tasks] == [
        "/backend-tasks-b2/do/math/insights_v2/2020"
    ]


@freeze_time("2020-04-01")
def test_enqueue_insights_v2_all(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights_v2/all")
    assert resp.status_code == 200
    assert resp.data == b"enqueued insights_v2 for all years"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    expected_years = list(SeasonHelper.get_valid_years())
    assert expected_years[-1] == 2020
    assert sorted(task.url for task in tasks) == sorted(
        f"/backend-tasks-b2/do/math/insights_v2/{year}" for year in expected_years
    )


def test_do_insights_v2_with_no_data(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights_v2/2024")
    assert resp.status_code == 200
    assert resp.data == b"[]"
    assert InsightV2.query().count() == 0


def test_do_insights_v2_writes_insights(
    tasks_cpu_client: Client, test_data_importer
) -> None:
    test_data_importer.import_event(
        __file__, "../../../common/helpers/tests/data/2024nytr.json"
    )
    test_data_importer.import_award_list(
        __file__, "../../../common/helpers/tests/data/2024nytr_awards.json"
    )

    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights_v2/2024")
    assert resp.status_code == 200

    stored = InsightV2.query().fetch()
    assert len(stored) > 0
    assert {insight.year for insight in stored} == {2024}
    assert resp.data.startswith(b"[InsightV2(")


def test_do_insights_delete(tasks_cpu_client: Client) -> None:
    name = Insight.INSIGHT_NAMES[Insight.NUM_MATCHES]
    create_insight(data=1, name=name, year=2022).put()
    create_insight(data=2, name=name, year=2023).put()
    create_insight(data=3, name=name, year=2023, district_abbreviation="fim").put()
    kept = create_insight(
        data=4, name=Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS], year=2023
    )
    kept.put()

    resp = tasks_cpu_client.get(f"/backend-tasks-b2/do/math/insights/delete/{name}")
    assert resp.status_code == 200
    assert len(resp.data) == 0

    assert [insight.key for insight in Insight.query().fetch()] == [kept.key]


def test_do_insights_v2_delete_by_name(tasks_cpu_client: Client) -> None:
    for year in [2025, 2026]:
        InsightV2(
            id=f"{year}_v2_leaderboard_most_division_wins",
            name="most_division_wins",
            display_name="Most Division Wins",
            year=year,
            category="leaderboard",
            data_json={},
        ).put()
    kept = InsightV2(
        id="2025_v2_leaderboard_other",
        name="other",
        display_name="Other",
        year=2025,
        category="leaderboard",
        data_json={},
    )
    kept.put()

    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/insights_v2/delete/most_division_wins"
    )
    assert resp.status_code == 200
    assert resp.data == b"deleted 2 insights_v2 named most_division_wins"
    assert [insight.key for insight in InsightV2.query().fetch()] == [kept.key]


def test_do_insights_v2_delete_by_name_and_year(tasks_cpu_client: Client) -> None:
    for year in [2025, 2026]:
        InsightV2(
            id=f"{year}_v2_leaderboard_most_division_wins",
            name="most_division_wins",
            display_name="Most Division Wins",
            year=year,
            category="leaderboard",
            data_json={},
        ).put()

    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/insights_v2/delete/most_division_wins/2025"
    )
    assert resp.status_code == 200
    assert resp.data == b"deleted 1 insights_v2 named most_division_wins"

    remaining = InsightV2.query().fetch()
    assert [insight.year for insight in remaining] == [2026]


def test_unknown_overall_insight_kind_outside_taskqueue_is_not_found(
    tasks_cpu_client: Client,
) -> None:
    """An unknown overall-insight kind is a client error and writes nothing."""
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/overallinsights/asdf")
    assert resp.status_code in (400, 404)
    assert Insight.query().count() == 0
