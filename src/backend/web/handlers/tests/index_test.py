from datetime import datetime
from typing import Any, cast

from flask import render_template
from werkzeug.test import Client

from backend.common.models.event import Event
from backend.web.handlers.index import _get_top_online_events_by_viewers


class _StubEvent:
    def __init__(self, online_webcasts: list[dict[str, Any]]) -> None:
        self.online_webcasts = online_webcasts


class _CompetitionSeasonTemplateEvent:
    def __init__(self) -> None:
        self.week = 0
        self.key_name = "2026test"
        self.name = "Test Event"
        self.city_state_country = None
        self.webcast: list[dict[str, Any]] = []
        self.now = False
        self.webcast_status = "offline"
        self.gameday_url = "/gameday"
        self.future = False
        self.within_a_day = False
        self.start_date = datetime(2026, 3, 1)
        self.end_date = datetime(2026, 3, 2)


def _make_event(online_webcasts: list[dict[str, Any]]) -> Event:
    return cast(Event, _StubEvent(online_webcasts))


def _render_competitionseason_template(
    events: list[Any],
    popular_online_events: list[Any],
) -> str:
    from backend.web.main import app

    with app.test_request_context("/"):
        return render_template(
            "index/index_competitionseason.html",
            events=events,
            any_webcast_online=False,
            special_webcasts=[],
            popular_teams_events=[],
            popular_online_events=popular_online_events,
        )


def test_index(web_client: Client) -> None:
    resp = web_client.get("/")
    assert resp.status_code == 200


def test_about(web_client: Client) -> None:
    resp = web_client.get("/about")
    assert resp.status_code == 200


def test_get_top_online_events_by_viewers_filters_to_online_events() -> None:
    offline_event = _make_event([{"status": "offline", "viewer_count": 1000}])
    unknown_event = _make_event([{"status": "unknown", "viewer_count": 500}])
    online_event = _make_event([{"status": "online", "viewer_count": 10}])

    top_online_events = _get_top_online_events_by_viewers(
        [offline_event, unknown_event, online_event]
    )

    assert top_online_events == [online_event]


def test_get_top_online_events_by_viewers_sorts_and_limits() -> None:
    events: list[Event] = [
        _make_event([{"status": "online", "viewer_count": viewer_count}])
        for viewer_count in range(12)
    ]

    top_online_events = _get_top_online_events_by_viewers(events, limit=10)

    assert len(top_online_events) == 10
    assert top_online_events[0] is events[11]
    assert top_online_events[-1] is events[2]


def test_get_top_online_events_by_viewers_uses_highest_webcast_viewers() -> None:
    multi_webcast_event = _make_event(
        [
            {"status": "online", "viewer_count": 20},
            {"status": "online", "viewer_count": 100},
        ]
    )
    lower_viewer_event = _make_event([{"status": "online", "viewer_count": 50}])

    top_online_events = _get_top_online_events_by_viewers(
        [lower_viewer_event, multi_webcast_event]
    )

    assert top_online_events == [multi_webcast_event, lower_viewer_event]


def test_competitionseason_hides_popular_events_tab_when_no_online_events() -> None:
    event = _CompetitionSeasonTemplateEvent()

    rendered = _render_competitionseason_template([event], [])

    assert 'href="#popular-events"' not in rendered
    assert 'id="popular-events"' not in rendered


def test_competitionseason_shows_popular_events_tab_when_online_events_exist() -> None:
    event = _CompetitionSeasonTemplateEvent()

    rendered = _render_competitionseason_template([event], [event])

    assert 'href="#popular-events"' in rendered
    assert 'id="popular-events"' in rendered
