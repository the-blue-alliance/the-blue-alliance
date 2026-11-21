import json

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_helper import InsightsHelper
from backend.common.models.event import Event
from backend.common.models.insight import Insight
from backend.common.models.match import Match


def test_overall_insights(web_client: Client) -> None:
    Insight(
        id=Insight.render_key_name(0, "blue_banners"),
        year=0,
        name="blue_banners",
        data_json=json.dumps({}),
    ).put()

    resp = web_client.get("/insights")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Most Blue Banners" in body


def test_detail_insights(web_client: Client) -> None:
    Insight(
        id=Insight.render_key_name(2022, "blue_banners"),
        year=2022,
        name="blue_banners",
        data_json=json.dumps({}),
    ).put()

    resp = web_client.get("/insights/2022")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Top Blue Banner Winners" in body


def test_detail_insights_badyear(web_client: Client) -> None:
    resp = web_client.get("/insights/1000")
    assert resp.status_code == 404


def test_detail_insights_2026_with_legacy_year_specific_data(
    web_client: Client,
) -> None:
    legacy_2026_insights = {"backfill_pending": True}

    Insight(
        id=Insight.render_key_name(2026, "year_specific_by_week"),
        year=2026,
        name="year_specific_by_week",
        data_json=json.dumps([]),
    ).put()

    Insight(
        id=Insight.render_key_name(2026, "year_specific"),
        year=2026,
        name="year_specific",
        data_json=json.dumps({"qual": legacy_2026_insights, "playoff": {}}),
    ).put()

    resp = web_client.get("/insights/2026")
    assert resp.status_code == 200

    body = resp.get_data(as_text=True)
    assert "Auto Win Conversion" in body
    assert "Fuel Statistics" in body
    assert "Tower Statistics" in body


def test_overall_insights_multiple(web_client: Client) -> None:
    for name in ["blue_banners", "ca_winner"]:
        Insight(
            id=Insight.render_key_name(0, name),
            year=0,
            name=name,
            data_json=json.dumps({}),
        ).put()

    resp = web_client.get("/insights")
    assert resp.status_code == 200


def test_detail_insights_highscore_match_has_rp_dot_tooltips(
    web_client: Client,
) -> None:
    event = Event(
        id="2019arc",
        year=2019,
        event_short="arc",
        event_type_enum=EventType.CMP_DIVISION,
        name="Archimedes Division",
    )
    match = Match(
        id="2019arc_qm82",
        event=ndb.Key(Event, "2019arc"),
        year=2019,
        comp_level="qm",
        set_number=1,
        match_number=82,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        alliances_json=json.dumps(
            {
                "red": {"teams": ["frc1", "frc2", "frc3"], "score": 100},
                "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 50},
            }
        ),
        score_breakdown_json=json.dumps(
            {
                "red": {"completeRocketRankingPoint": True},
                "blue": {"habDockingRankingPoint": True},
            }
        ),
    )
    match_data = InsightsHelper._generateMatchData(match, event)
    Insight(
        id=Insight.render_key_name(2019, "match_highscore"),
        year=2019,
        name="match_highscore",
        data_json=json.dumps({"qual": [match_data], "playoff": [], "overall": []}),
    ).put()
    Insight(
        id=Insight.render_key_name(2019, "match_highscore_by_week"),
        year=2019,
        name="match_highscore_by_week",
        data_json=json.dumps([]),
    ).put()

    resp = web_client.get("/insights/2019")
    assert resp.status_code == 200

    body = resp.get_data(as_text=True)
    assert 'class="top-left-dot" rel="tooltip" title="Complete Rocket"' in body
    assert 'class="top-left-dot-2" rel="tooltip" title="HAB Docking"' in body
