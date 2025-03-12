from unittest import mock

from werkzeug.test import Client

from backend.common.futures import InstantFuture
from backend.common.models.district import District
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


def test_district_list_bad_year(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/district_list/asdf")
    assert resp.status_code == 404


@mock.patch.object(DatafeedFMSAPI, "get_district_list")
def test_district_list_get_year(api_mock, tasks_client: Client) -> None:
    api_mock.return_value = InstantFuture(
        [District(id="2020ne", year=2020, abbreviation="ne")]
    )

    resp = tasks_client.get("/backend-tasks/get/district_list/2020")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Ensure we created models
    assert District.get_by_id("2020ne") is not None


@mock.patch.object(DatafeedFMSAPI, "get_district_list")
def test_district_list_get_year_no_output_in_taskqueue(
    api_mock, tasks_client: Client
) -> None:
    api_mock.return_value = InstantFuture(
        [District(id="2020ne", year=2020, abbreviation="ne")]
    )

    resp = tasks_client.get(
        "/backend-tasks/get/district_list/2020",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    # Ensure we created models
    assert District.get_by_id("2020ne") is not None


def test_district_rankings_bad_key(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/district_rankings/asdf")
    assert resp.status_code == 404


def test_district_rankings_no_district(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/district_rankings/2020ne")
    assert resp.status_code == 404


@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_district_rankings(api_mock, tasks_client: Client) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()
    advancement = {"frc254": {"dcmp": True, "cmp": True}}
    api_mock.return_value = InstantFuture(advancement)

    resp = tasks_client.get(
        "/backend-tasks/get/district_rankings/2020ne",
    )
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Ensure we created models
    d = District.get_by_id("2020ne")
    assert d is not None
    assert d.advancement == advancement


@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_district_rankings_no_output_in_taskqueue(
    api_mock, tasks_client: Client
) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()
    advancement = {"frc254": {"dcmp": True, "cmp": True}}
    api_mock.return_value = InstantFuture(advancement)

    resp = tasks_client.get(
        "/backend-tasks/get/district_rankings/2020ne",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    # Ensure we created models
    d = District.get_by_id("2020ne")
    assert d is not None
    assert d.advancement == advancement
