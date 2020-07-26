from bs4 import BeautifulSoup
from werkzeug.test import Client


def test_get_bad_match_key(web_client: Client) -> None:
    resp = web_client.get("/match/2020nyny_qm1")
    assert resp.status_code == 404


def test_render_match(web_client: Client, setup_full_match) -> None:
    setup_full_match("2019nyny_qm1")

    resp = web_client.get("/match/2019nyny_qm1")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert (
        " ".join(soup.find(id="match-title").stripped_strings)
        == "Quals 1 New York City Regional 2019"
    )
    assert soup.find(id="match-table-2019nyny_qm1") is not None
    assert soup.find(id="match-breakdown") is not None
    assert soup.find(id="youtube_ooI6fkKfzLc") is not None
