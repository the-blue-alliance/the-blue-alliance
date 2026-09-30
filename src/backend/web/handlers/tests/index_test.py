import json
from datetime import datetime, timedelta
from typing import Any, cast, List

import pytest
from flask import render_template
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.consts.landing_type import LandingType
from backend.common.consts.media_type import MediaType
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.memcache import MemcacheClient
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.insight import Insight
from backend.common.models.media import Media
from backend.common.models.webcast import Webcast
from backend.common.sitevars.gameday_special_webcasts import GamedaySpecialWebcasts
from backend.common.sitevars.landing_config import LandingConfig
from backend.web.handlers.conftest import CapturedTemplate
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


# ---------------------------------------------------------------------------
# Landing pages
# ---------------------------------------------------------------------------


def _set_landing(landing_type: LandingType) -> None:
    config = LandingConfig.default_value()
    config["current_landing"] = int(landing_type)
    LandingConfig.put(config)


def _put_event(
    event_short: str,
    start: datetime,
    end: datetime,
    event_type: EventType = EventType.REGIONAL,
    webcasts: list[dict[str, str]] | None = None,
) -> Event:
    year = datetime.now().year
    event = Event(
        id=f"{year}{event_short}",
        year=year,
        event_short=event_short,
        name=f"Event {event_short}",
        event_type_enum=event_type,
        start_date=start,
        end_date=end,
        webcast_json=json.dumps(webcasts) if webcasts else None,
    )
    event.put()
    return event


def test_index_kickoff(
    ndb_stub, captured_templates: List[CapturedTemplate], web_client: Client
) -> None:
    _set_landing(LandingType.KICKOFF)

    resp = web_client.get("/")

    assert resp.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "index/index_kickoff.html"
    year = SeasonHelper.effective_season_year()
    assert context["year"] == year
    assert context["is_kickoff"] == SeasonHelper.is_kickoff_at_least_one_day_away(
        year=year
    )
    assert context["kickoff_datetime_est"] == SeasonHelper.kickoff_datetime_est(year)
    assert context["kickoff_datetime_utc"] == SeasonHelper.kickoff_datetime_utc(year)
    # LandingConfig values are passed through to the template
    assert context["game_teaser_youtube_id"] == ""


def test_index_buildseason(
    ndb_stub, captured_templates: List[CapturedTemplate], web_client: Client
) -> None:
    _set_landing(LandingType.BUILDSEASON)

    resp = web_client.get("/")

    assert resp.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "index/index_buildseason.html"
    assert context["year"] == SeasonHelper.effective_season_year()
    assert context["seasonstart_datetime_utc"] is None
    assert context["events"] == []
    assert context["any_webcast_online"] is False
    assert context["special_webcasts"] == []


def test_index_competitionseason(
    ndb_stub, captured_templates: List[CapturedTemplate], web_client: Client
) -> None:
    _set_landing(LandingType.COMPETITIONSEASON)
    now = datetime.now()

    # A live event streaming on the FIRST channel, a live event with no
    # webcast, and an upcoming event later this week
    live = _put_event(
        "live",
        now - timedelta(days=1),
        now + timedelta(days=1),
        webcasts=[{"type": "twitch", "channel": "firstinspires"}],
    )
    _put_event("quiet", now - timedelta(days=1), now + timedelta(days=1))
    _put_event(
        "soon",
        now + timedelta(days=2),
        now + timedelta(days=4),
        webcasts=[{"type": "twitch", "channel": "firstinspires2"}],
    )
    WebcastOnlineStatusMemcache(
        Webcast(type=WebcastType.TWITCH, channel="firstinspires")
    ).put(
        Webcast(
            type=WebcastType.TWITCH,
            channel="firstinspires",
            status=WebcastStatus.ONLINE,
            viewer_count=1234,
        )
    )

    # Two special webcasts: one duplicates the live event's stream and is
    # hidden; the other is shown and is online
    GamedaySpecialWebcasts.put(
        {
            "default_chat": "tbagameday",
            "webcasts": [
                {
                    "type": WebcastType.TWITCH,
                    "channel": "firstinspires",
                    "name": "FIRST",
                    "key_name": "first",
                },
                {
                    "type": WebcastType.TWITCH,
                    "channel": "tbagameday",
                    "name": "TBA GameDay",
                    "key_name": "tba",
                },
            ],
            "aliases": {},
        }
    )
    WebcastOnlineStatusMemcache(
        Webcast(type=WebcastType.TWITCH, channel="tbagameday")
    ).put(
        Webcast(
            type=WebcastType.TWITCH, channel="tbagameday", status=WebcastStatus.ONLINE
        )
    )

    resp = web_client.get("/")

    assert resp.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "index/index_competitionseason.html"
    assert sorted(e.key_name for e in context["events"]) == sorted(
        [f"{now.year}live", f"{now.year}quiet", f"{now.year}soon"]
    )
    assert [w["channel"] for w in context["special_webcasts"]] == ["tbagameday"]
    assert context["any_webcast_online"] is True
    assert context["popular_teams_events"] == []
    assert [e.key_name for e in context["popular_online_events"]] == [live.key_name]


def test_index_champs(
    ndb_stub, captured_templates: List[CapturedTemplate], web_client: Client
) -> None:
    _set_landing(LandingType.CHAMPS)
    now = datetime.now()
    division = _put_event(
        "arc", now, now + timedelta(days=3), event_type=EventType.CMP_DIVISION
    )
    finals = _put_event(
        "cmptx", now, now + timedelta(days=3), event_type=EventType.CMP_FINALS
    )
    _put_event("reg", now, now + timedelta(days=3))

    resp = web_client.get("/")

    assert resp.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "index/index_champs.html"
    assert context["year"] == now.year
    assert sorted(e.key_name for e in context["events"]) == sorted(
        [division.key_name, finals.key_name]
    )


def test_index_offseason(
    ndb_stub, captured_templates: List[CapturedTemplate], web_client: Client
) -> None:
    _set_landing(LandingType.OFFSEASON)

    resp = web_client.get("/")

    assert resp.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "index/index_offseason.html"
    year = SeasonHelper.effective_season_year()
    assert context["year"] == year
    assert context["kickoff_datetime_utc"] == SeasonHelper.kickoff_datetime_utc(year)
    assert context["events"] == []
    assert context["any_webcast_online"] is False
    assert context["special_webcasts"] == []


def test_index_insights(
    ndb_stub, captured_templates: List[CapturedTemplate], web_client: Client
) -> None:
    _set_landing(LandingType.INSIGHTS)
    year = datetime.now().year
    Insight(
        id=Insight.render_key_name(year, "num_matches"),
        year=year,
        name="num_matches",
        data_json=json.dumps(1234),
    ).put()
    Insight(
        id=Insight.render_key_name(year, "match_highscore"),
        year=year,
        name="match_highscore",
        data_json=json.dumps({"qual": [], "playoff": []}),
    ).put()

    resp = web_client.get("/")

    assert resp.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "index/index_insights.html"
    assert context["year"] == year
    assert context["events"] == []
    assert context["any_webcast_online"] is False
    assert context["num_matches"].data == 1234
    assert context["match_highscore"].data == {"qual": [], "playoff": []}
    # Insights that don't exist for the year are simply absent
    assert "blue_banners" not in context


# ---------------------------------------------------------------------------
# Avatars
# ---------------------------------------------------------------------------


def _put_avatar(year: int, team_number: int) -> Media:
    foreign_key = f"avatar_{year}_frc{team_number}"
    avatar = Media(
        id=Media.render_key_name(MediaType.AVATAR, foreign_key),
        media_type_enum=MediaType.AVATAR,
        foreign_key=foreign_key,
        references=[ndb.Key("Team", f"frc{team_number}")],
        year=year,
        details_json=json.dumps({"base64Image": ""}),
    )
    avatar.put()
    return avatar


@pytest.mark.parametrize("year", [2017, 2021, 3000])
def test_avatar_list_invalid_year(ndb_stub, year: int, web_client: Client) -> None:
    resp = web_client.get(f"/avatars/{year}")
    assert resp.status_code == 404


def test_avatar_list_defaults_to_current_season(
    ndb_stub, captured_templates: List[CapturedTemplate], web_client: Client
) -> None:
    resp = web_client.get("/avatars")

    assert resp.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "avatars.html"
    assert context["year"] == SeasonHelper.get_current_season()
    assert 2021 not in context["valid_years"]
    assert context["valid_years"][0] == 2018
    assert context["valid_years"][-1] == SeasonHelper.get_max_year()
    assert context["avatars"] == []


def test_avatar_list_sorts_by_team_and_caches_shards(
    ndb_stub, captured_templates: List[CapturedTemplate], web_client: Client
) -> None:
    for team_number in [1114, 254, 604]:
        _put_avatar(2024, team_number)
    _put_avatar(2023, 33)  # other year
    # An avatar with no team reference is dropped
    Media(
        id=Media.render_key_name(MediaType.AVATAR, "avatar_2024_orphan"),
        media_type_enum=MediaType.AVATAR,
        foreign_key="avatar_2024_orphan",
        references=[],
        year=2024,
        details_json=json.dumps({"base64Image": ""}),
    ).put()

    resp = web_client.get("/avatars/2024")

    assert resp.status_code == 200
    context = captured_templates[0][1]
    assert context["year"] == 2024
    assert [a.references[0].id() for a in context["avatars"]] == [
        "frc254",
        "frc604",
        "frc1114",
    ]

    # The avatars were written to memcache in 20 shards
    shards = MemcacheClient.get().get_multi(
        [f"2024avatars_{i}".encode("utf-8") for i in range(20)]
    )
    assert len(shards) == 20
    assert sum(len(shard) for shard in shards.values()) == 3

    # A second request (different query string, so it isn't served from the
    # response cache) is assembled from the memcache shards
    resp = web_client.get("/avatars/2024?fresh=1")

    assert resp.status_code == 200
    context = captured_templates[1][1]
    assert [a.references[0].id() for a in context["avatars"]] == [
        "frc254",
        "frc604",
        "frc1114",
    ]


def test_avatar_list_cached_shards_are_reassembled_out_of_order(
    ndb_stub, captured_templates: List[CapturedTemplate], web_client: Client
) -> None:
    # BUG: shards are reassembled in lexicographic key order
    # ("..._1", "..._10", "..._11", ..., "..._19", "..._2", ...) rather than
    # numeric order, so once more than 10 shards are populated the cached page
    # is no longer sorted by team number. Documented here rather than fixed;
    # see the PR description.
    team_numbers = list(range(1, 26))
    for team_number in team_numbers:
        _put_avatar(2024, team_number)

    resp = web_client.get("/avatars/2024")
    assert resp.status_code == 200
    fresh_order = [a.references[0].id() for a in captured_templates[0][1]["avatars"]]
    assert fresh_order == [f"frc{n}" for n in team_numbers]

    resp = web_client.get("/avatars/2024?fresh=1")
    assert resp.status_code == 200
    cached_order = [a.references[0].id() for a in captured_templates[1][1]["avatars"]]
    assert sorted(cached_order, key=lambda k: int(k[3:])) == fresh_order
    assert cached_order != fresh_order
