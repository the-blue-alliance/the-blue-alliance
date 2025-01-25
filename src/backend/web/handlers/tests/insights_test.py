import json

from werkzeug.test import Client

from backend.common.models.insight import Insight


def test_overall_insights(web_client: Client) -> None:
    Insight(
        id=Insight.render_key_name(0, "blue_banners", None),
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
        id=Insight.render_key_name(2022, "blue_banners", None),
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
