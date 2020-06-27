from backend.common.models.event_details import EventDetails
from backend.common.queries.event_details_query import EventDetailsQuery


def test_event_details_not_found() -> None:
    details = EventDetailsQuery(event_key="2019nyny").fetch()
    assert details is None


def test_event_details_is_found() -> None:
    EventDetails(id="2019nyny").put()
    result = EventDetailsQuery(event_key="2019nyny").fetch()
    assert result is not None
    assert result.year == 2019
    assert result.key_name == "2019nyny"
