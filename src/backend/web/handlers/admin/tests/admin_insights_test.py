import bs4
from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.helpers.insights_helper_utils import create_insight
from backend.common.models.insight import Insight


def test_insights_list_empty(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/insights")
    assert resp.status_code == 200


@freeze_time("2026-03-01")
def test_insights_list_defaults_to_current_season(
    web_client: Client, login_gae_admin
) -> None:
    resp = web_client.get("/admin/insights")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert "2026" in soup.find("title").get_text()


def test_insights_list_explicit_year(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/insights/2023")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert "2023" in soup.find("title").get_text()


def test_insights_list_shows_global_insights(
    web_client: Client, login_gae_admin
) -> None:
    insight = create_insight(
        data={"test": 123},
        name=Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
        year=2023,
    )
    insight.put()

    resp = web_client.get("/admin/insights/2023")
    assert resp.status_code == 200

    assert Insight.INSIGHT_NAMES[Insight.NUM_MATCHES] in resp.data.decode()


def test_insights_list_shows_district_insights(
    web_client: Client, login_gae_admin
) -> None:
    insight = create_insight(
        data={"test": 456},
        name=Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
        year=2023,
        district_abbreviation="fim",
    )
    insight.put()

    resp = web_client.get("/admin/insights/2023")
    assert resp.status_code == 200

    body = resp.data.decode()
    assert "fim" in body
    assert Insight.INSIGHT_NAMES[Insight.NUM_MATCHES] in body


def test_insights_list_enqueue_buttons_present(
    web_client: Client, login_gae_admin
) -> None:
    resp = web_client.get("/admin/insights/2023")
    assert resp.status_code == 200

    body = resp.data.decode()
    assert "/backend-tasks-b2/enqueue/math/insights/matches/2023" in body
    assert "/backend-tasks-b2/enqueue/math/insights/awards/2023" in body
    assert "/backend-tasks-b2/enqueue/math/insights/predictions/2023" in body
    assert "/backend-tasks-b2/enqueue/math/insights/districts/2023" in body
    assert "/backend-tasks-b2/enqueue/math/overallinsights/matches" in body
    assert "/backend-tasks-b2/enqueue/math/overallinsights/awards" in body
