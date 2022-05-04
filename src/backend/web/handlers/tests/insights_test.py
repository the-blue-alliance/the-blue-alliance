from werkzeug.test import Client


def test_overall_insights(web_client: Client) -> None:
    resp = web_client.get("/insights")
    assert resp.status_code == 200


def test_detail_insights(web_client: Client) -> None:
    resp = web_client.get("/insights/2022")
    assert resp.status_code == 200


def test_detail_insights_badyear(web_client: Client) -> None:
    resp = web_client.get("/insights/1000")
    assert resp.status_code == 404
