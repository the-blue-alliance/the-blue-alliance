import json
import os
import re
from datetime import datetime

from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.helpers.nexus_pit_map_svg_helper import NexusEventDetailsSVGHelper
from backend.common.models.event import Event
from backend.common.models.nexus_event_details import NexusEventDetails
from backend.web.handlers.tests import helpers


def _load_fixture(filename: str) -> str:
    fixture_path = os.path.join(os.path.dirname(__file__), "data", filename)
    with open(fixture_path) as fixture_file:
        return fixture_file.read()


def _normalize_svg(svg: str) -> str:
    normalized = re.sub(r">\s+<", "><", svg)
    return re.sub(r"\s+", " ", normalized).strip()


def _assert_matches_light_and_dark(actual_svg: str, base_name: str) -> None:
    light_expected = _load_fixture(f"{base_name}_light.svg")
    dark_expected = _load_fixture(f"{base_name}_dark.svg")
    assert _normalize_svg(
        NexusEventDetailsSVGHelper.force_light_color_scheme(actual_svg)
    ) == _normalize_svg(light_expected)
    assert _normalize_svg(
        NexusEventDetailsSVGHelper.force_dark_color_scheme(actual_svg)
    ) == _normalize_svg(dark_expected)


def test_event_pitmap_400_when_event_key_invalid(web_client: Client) -> None:
    resp = web_client.get("/event/not-a-real-key/pitmap")
    assert resp.status_code == 400


def test_event_pitmap_404_when_event_missing(web_client: Client) -> None:
    resp = web_client.get("/event/2026nyny/pitmap")
    assert resp.status_code == 404


def test_event_pitmap_404_when_map_missing(ndb_stub, web_client: Client) -> None:
    helpers.preseed_event("2020nyny")

    resp = web_client.get("/event/2020nyny/pitmap")
    assert resp.status_code == 404


def test_event_pitmap_renders_svg_with_long_cache(ndb_stub, web_client: Client) -> None:
    Event(
        id="2019nyny",
        event_short="nyny",
        year=2019,
        name="Test Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2019, 3, 1),
        end_date=datetime(2019, 3, 5),
    ).put()

    NexusEventDetails(
        id="2019nyny",
        pitmap_json={
            "size": {"x": 100, "y": 100},
            "pits": {
                "A1": {
                    "position": {"x": 50, "y": 50},
                    "size": {"x": 40, "y": 40},
                    "team": "1678",
                }
            },
            "areas": None,
            "labels": None,
            "arrows": None,
            "walls": None,
        },
    ).put()

    resp = web_client.get("/event/2019nyny/pitmap")

    assert resp.status_code == 200
    assert "max-age=21600" in resp.headers["Cache-Control"]
    assert resp.headers["content-type"] == "image/svg+xml; charset=UTF-8"

    body = resp.get_data(as_text=True)
    assert "<svg" in body
    assert "A1" in body
    assert "1678" in body
    assert "https://frc.nexus/2019nyny/pits" in body


@freeze_time("2020-03-02")
def test_event_pitmap_uses_short_cache_for_active_event(
    ndb_stub, web_client: Client
) -> None:
    helpers.preseed_event("2020nyny")
    NexusEventDetails(
        id="2020nyny",
        pitmap_json={
            "size": {"x": 100, "y": 100},
            "pits": {
                "A1": {
                    "position": {"x": 50, "y": 50},
                    "size": {"x": 40, "y": 40},
                }
            },
            "areas": None,
            "labels": None,
            "arrows": None,
            "walls": None,
        },
    ).put()

    resp = web_client.get("/event/2020nyny/pitmap")

    assert resp.status_code == 200
    assert "max-age=61" in resp.headers["Cache-Control"]


def test_event_pitmap_matches_nysu_golden_svg(ndb_stub, web_client: Client) -> None:
    Event(
        id="2026nysu",
        event_short="nysu",
        year=2026,
        name="NYSU Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 5),
    ).put()

    NexusEventDetails(
        id="2026nysu",
        pitmap_json=json.loads(_load_fixture("2026nysu_pitmap.json")),
    ).put()

    resp = web_client.get("/event/2026nysu/pitmap")
    assert resp.status_code == 200

    _assert_matches_light_and_dark(
        resp.get_data(as_text=True), "2026nysu_pitmap_expected"
    )


def test_event_pitmap_matches_nyny_golden_svg(ndb_stub, web_client: Client) -> None:
    Event(
        id="2026nyny",
        event_short="nyny",
        year=2026,
        name="NYNY Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 5),
    ).put()

    NexusEventDetails(
        id="2026nyny",
        pitmap_json=json.loads(_load_fixture("2026nyny_pitmap.json")),
    ).put()

    resp = web_client.get("/event/2026nyny/pitmap")
    assert resp.status_code == 200

    _assert_matches_light_and_dark(
        resp.get_data(as_text=True), "2026nyny_pitmap_expected"
    )


def test_event_pitmap_matches_nyny_highlight_golden_svg(
    ndb_stub, web_client: Client
) -> None:
    Event(
        id="2026nyny",
        event_short="nyny",
        year=2026,
        name="NYNY Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 5),
    ).put()

    NexusEventDetails(
        id="2026nyny",
        pitmap_json=json.loads(_load_fixture("2026nyny_pitmap.json")),
    ).put()

    resp = web_client.get("/event/2026nyny/pitmap?teams=frc3015")
    assert resp.status_code == 200

    _assert_matches_light_and_dark(
        resp.get_data(as_text=True), "2026nyny_pitmap_team3015_expected"
    )


def test_event_pitmap_matches_nysu_highlight_golden_svg(
    ndb_stub, web_client: Client
) -> None:
    Event(
        id="2026nysu",
        event_short="nysu",
        year=2026,
        name="NYSU Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 5),
    ).put()

    NexusEventDetails(
        id="2026nysu",
        pitmap_json=json.loads(_load_fixture("2026nysu_pitmap.json")),
    ).put()

    resp = web_client.get("/event/2026nysu/pitmap?teams=frc1796")
    assert resp.status_code == 200

    _assert_matches_light_and_dark(
        resp.get_data(as_text=True), "2026nysu_pitmap_team1796_expected"
    )


def test_event_pitmap_teams_supports_list_of_team_keys(
    ndb_stub, web_client: Client
) -> None:
    Event(
        id="2026nysu",
        event_short="nysu",
        year=2026,
        name="NYSU Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 5),
    ).put()

    NexusEventDetails(
        id="2026nysu",
        pitmap_json=json.loads(_load_fixture("2026nysu_pitmap.json")),
    ).put()

    resp = web_client.get("/event/2026nysu/pitmap?teams=frc10922&teams=frc1796")
    assert resp.status_code == 200

    body = resp.get_data(as_text=True)
    assert body.count('class="pit pit-highlighted"') == 2


def test_event_pitmap_teams_supports_comma_separated_team_keys(
    ndb_stub, web_client: Client
) -> None:
    Event(
        id="2026nysu",
        event_short="nysu",
        year=2026,
        name="NYSU Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 5),
    ).put()

    NexusEventDetails(
        id="2026nysu",
        pitmap_json=json.loads(_load_fixture("2026nysu_pitmap.json")),
    ).put()

    resp = web_client.get("/event/2026nysu/pitmap?teams=frc10922,frc1796")
    assert resp.status_code == 200

    body = resp.get_data(as_text=True)
    assert body.count('class="pit pit-highlighted"') == 2


def test_event_pitmap_400_when_teams_param_contains_invalid_team_key(
    ndb_stub, web_client: Client
) -> None:
    helpers.preseed_event("2026nyny")
    NexusEventDetails(
        id="2026nyny",
        pitmap_json={"size": {"x": 100, "y": 100}, "pits": {}},
    ).put()

    resp = web_client.get("/event/2026nyny/pitmap?teams=3015")
    assert resp.status_code == 400
