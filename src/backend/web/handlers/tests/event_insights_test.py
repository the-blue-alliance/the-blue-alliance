from werkzeug.test import Client

from backend.common.models.event_details import EventDetails
from backend.web.handlers.tests import helpers


def test_bad_event_key(web_client: Client) -> None:
    resp = web_client.get("/event/asdf/insights")
    assert resp.status_code == 404


def test_old_event(web_client: Client, ndb_stub) -> None:
    helpers.preseed_event("2015nyny")

    resp = web_client.get("/event/2015nyny/insights")
    assert resp.status_code == 404


def test_no_details(web_client: Client, ndb_stub) -> None:
    helpers.preseed_event("2019nyny")

    resp = web_client.get("/event/2019nyny/insights")
    assert resp.status_code == 404


def test_no_predictions(web_client: Client, ndb_stub) -> None:
    helpers.preseed_event("2019nyny")
    EventDetails(id="2019nyny").put()

    resp = web_client.get("/event/2019nyny/insights")
    assert resp.status_code == 404


def test_full_predictions(
    web_client: Client, ndb_stub, setup_full_event, setup_event_preductions
) -> None:
    setup_full_event("2019nyny")
    setup_event_preductions("2019nyny")

    resp = web_client.get("/event/2019nyny/insights")
    assert resp.status_code == 200


def test_predictions_no_matches(
    web_client: Client, ndb_stub, setup_event_preductions
) -> None:
    helpers.preseed_event("2019nyny")
    setup_event_preductions("2019nyny")

    resp = web_client.get("/event/2019nyny/insights")
    assert resp.status_code == 200
